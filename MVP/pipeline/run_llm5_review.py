from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[1]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import write_text  # noqa: E402
from pipeline.preflight import check_codegen  # noqa: E402
from pipeline.rendering import detect_scene_classes  # noqa: E402
from pipeline.run_layout import RunLayout  # noqa: E402
from pipeline.run_mvp import build_client, stage_fix_code  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="LLM5（review）：静态审查并预修复 llm4 生成的 Manim 代码（不需要 stderr）"
    )
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（包含 llm4/scene.py）")
    p.add_argument("--py", type=str, default="llm4/scene.py", help="要审查/修复的 Python 文件")
    p.add_argument("--attempt", type=int, default=0, help="写 fix_raw_<attempt>.txt（默认 0）")
    p.add_argument("--class-name", type=str, default="", help="可选：显式指定目标 Scene 类名")
    p.add_argument("--force", action="store_true", help="即使未发现问题也强制跑一次 Fixer")
    return p.parse_args()


def _load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _resolve_class_name(args: argparse.Namespace, layout: RunLayout, code: str) -> str:
    if args.class_name and args.class_name.strip():
        return args.class_name.strip()

    meta = _load_json_if_exists(layout.stage4_meta)
    class_name = str(meta.get("class_name") or "").strip()
    if class_name:
        return class_name

    classes = detect_scene_classes(code)
    if classes:
        return classes[0]

    return "MainScene"


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")
    layout = RunLayout.from_run_dir(run_dir)

    py_path = (run_dir / args.py).resolve() if not Path(args.py).is_absolute() else Path(args.py)
    if not py_path.exists():
        raise SystemExit(f"缺少代码文件: {py_path}")

    code = py_path.read_text(encoding="utf-8")
    class_name = _resolve_class_name(args, layout, code)

    pre = check_codegen(code=code, expected_class_name=class_name)
    report_lines = ["【Preflight 静态审查报告】", f"- ok: {pre.ok}", f"- expected_class: {class_name}"]
    report_lines.extend([f"- {x}" for x in pre.issues])
    report = "\n".join(report_lines) + "\n"
    write_text(layout.llm5_dir / "preflight_report.txt", report)

    if pre.ok and not args.force:
        print("[LLM5-review] 未发现需要修复的问题，跳过。")
        return 0

    client = build_client()
    system = client.load_stage_system_prompt("fixer")
    write_text(layout.llm5_system_prompt, system.strip() + "\n")

    fixed = stage_fix_code(
        client,
        class_name=class_name,
        code=code,
        stderr=report,
        scene_dir=layout.llm5_dir,
        attempt=max(0, int(args.attempt)),
    )
    write_text(py_path, fixed)

    # 同步导出：llm4/scene.py <-> run_dir/scene.py
    try:
        if py_path.resolve() == layout.llm4_scene_py.resolve():
            write_text(layout.exported_scene_py, fixed)
        elif py_path.resolve() == layout.exported_scene_py.resolve():
            write_text(layout.llm4_scene_py, fixed)
    except Exception:  # noqa: BLE001
        pass

    # 更新 meta
    classes = detect_scene_classes(fixed)
    new_class = classes[0] if classes else class_name
    meta_path = layout.stage4_meta
    meta = _load_json_if_exists(meta_path)
    meta.update({"class_name": new_class, "last_review_attempt": max(0, int(args.attempt))})
    write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    print(f"[LLM5-review] 已修复并写回: {py_path}（class_name={new_class}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

