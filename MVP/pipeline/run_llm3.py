from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[1]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import list_scenes, load_json, pick_scenes, read_requirement, write_text  # noqa: E402
from pipeline.run_mvp import (  # noqa: E402
    build_client,
    generate_scene_designs_batch,
    generate_scene_design,
    reset_case_outputs,
    write_split_scene_design_files,
)
from pipeline.run_layout import RunLayout  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM3（scene_designer）：逐分镜生成 scene 设计稿（聚合输出）")
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（需要 llm1/llm2 输出）")
    p.add_argument("--scene-id", type=str, default="", help="只生成指定 scene_id（会更新聚合文件）")
    p.add_argument("--force", action="store_true", help="已废弃参数（兼容保留，不再使用）")
    return p.parse_args()


def _index_by_scene_id(items: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        sid = str(it.get("scene_id") or "").strip()
        if sid:
            out[sid] = it
    return out


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")
    layout = RunLayout.from_run_dir(run_dir)
    stale_boundary_file = layout.llm3_dir / "object_boundary_memory.json"
    if stale_boundary_file.exists():
        stale_boundary_file.unlink()
    if args.scene_id.strip():
        raw_path = layout.stage3_raw_scene(args.scene_id)
        if raw_path.exists():
            raw_path.unlink()
        reset_case_outputs(layout, from_stage=4)
    else:
        reset_case_outputs(layout, from_stage=3)

    requirement = read_requirement(run_dir=run_dir)

    analyst_path = layout.stage1_json
    plan_path = layout.stage2_json
    if not analyst_path.exists():
        # 兼容旧布局：<run_dir>/stage1_analyst.json
        legacy = run_dir / "stage1_analyst.json"
        if legacy.exists():
            analyst_path = legacy
    if not plan_path.exists():
        # 兼容旧布局：<run_dir>/stage2_scene_plan.json
        legacy = run_dir / "stage2_scene_plan.json"
        if legacy.exists():
            plan_path = legacy
    if not analyst_path.exists():
        raise SystemExit(f"缺少: {analyst_path}（请先运行 run_llm1.py）")
    if not plan_path.exists():
        raise SystemExit(f"缺少: {plan_path}（请先运行 run_llm2.py）")

    analyst = load_json(analyst_path)
    plan = load_json(plan_path)

    scenes = pick_scenes(plan, scene_id=args.scene_id)
    if not scenes:
        raise SystemExit("未找到要运行的 scenes（检查 stage2_scene_plan.json 或 --scene-id）")

    all_scenes = plan.get("scenes") or []
    if not isinstance(all_scenes, list):
        all_scenes = []
    all_scenes = [sc for sc in all_scenes if isinstance(sc, dict)]
    scene_index_by_id = {
        str(sc.get("scene_id") or "").strip(): idx for idx, sc in enumerate(all_scenes)
    }

    client = build_client()
    system = client.load_stage_system_prompt("scene_designer")
    write_text(layout.llm3_system_prompt, system.strip() + "\n")

    stage3_path = layout.stage3_json
    if not args.scene_id.strip():
        payload, raw = generate_scene_designs_batch(
            client,
            requirement=requirement,
            analyst=analyst,
            plan=plan,
        )
        write_text(layout.stage3_raw_batch, raw)
        write_text(stage3_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_split_scene_design_files(out_dir=layout.llm3_dir, scene_designs=payload)
        print(f"[LLM3] 完成: {len(payload.get('scenes') or [])} 个。输出: {stage3_path}")
        return 0

    existing_payload: dict[str, Any] = {}
    if stage3_path.exists():
        try:
            existing_payload = load_json(stage3_path)
        except Exception:  # noqa: BLE001
            existing_payload = {}

    video_title = str(plan.get("video_title") or "").strip()
    if isinstance(existing_payload, dict):
        video_title = str(existing_payload.get("video_title") or video_title).strip()

    existing_map = _index_by_scene_id(existing_payload.get("scenes") if isinstance(existing_payload, dict) else None)

    ran = 0
    for scene in scenes:
        sid = str(scene.get("scene_id") or "").strip() or "scene_unknown"
        full_idx = scene_index_by_id.get(sid, -1)
        prev_scene = all_scenes[full_idx - 1] if full_idx > 0 else None
        previous_scene_design = (
            existing_map.get(str(prev_scene.get("scene_id") or "").strip())
            if isinstance(prev_scene, dict)
            else None
        )

        design, raw = generate_scene_design(
            client,
            requirement=requirement,
            analyst=analyst,
            scene=scene,
            prev_scene=prev_scene,
            next_scene=all_scenes[full_idx + 1]
            if 0 <= full_idx + 1 < len(all_scenes)
            else None,
            previous_scene_design=previous_scene_design,
            plan=plan,
        )
        write_text(layout.stage3_raw_scene(sid), raw)
        existing_map[sid] = design
        ran += 1

    # 按 planner 的顺序落盘，确保可复现
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sc in list_scenes(plan):
        sid = str(sc.get("scene_id") or "").strip()
        if not sid:
            continue
        it = existing_map.get(sid)
        if it is None:
            continue
        ordered.append(it)
        seen.add(sid)

    # 兜底：把旧文件里存在但 planner 里找不到的内容也追加（避免误丢）
    for sid, it in existing_map.items():
        if sid not in seen:
            ordered.append(it)

    payload = {"video_title": video_title, "scenes": ordered}
    write_text(stage3_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_split_scene_design_files(out_dir=layout.llm3_dir, scene_designs=payload)

    print(f"[LLM3] 完成: {ran} 个。输出: {stage3_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
