from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# 允许两种运行方式：
# 1) 推荐：在 MVP/ 目录内执行：python run_mvp.py
# 2) 兼容：直接执行：python pipeline/run_mvp.py
#
# 注意：第二种方式下需要手动把 MVP 根目录加入 sys.path，保证能正确导入 package。
if __package__ in {None, ""}:
    _mvp_root = Path(__file__).resolve().parents[1]
    if str(_mvp_root) not in sys.path:
        sys.path.insert(0, str(_mvp_root))

    from pipeline.config import ERROR_DIR, PROMPTS_DIR, RUNS_DIR  # noqa: E402
    from pipeline.llm_client import LLMClient, LLMStage  # noqa: E402
    from pipeline.run_layout import RunLayout  # noqa: E402
    from pipeline.static_checks import run_static_checks  # noqa: E402
    from pipeline.rendering import (  # noqa: E402
        detect_scene_classes,
        render_scene,
    )
else:
    from .config import ERROR_DIR, PROMPTS_DIR, RUNS_DIR  # noqa: E402
    from .llm_client import LLMClient, LLMStage  # noqa: E402
    from .run_layout import RunLayout  # noqa: E402
    from .static_checks import run_static_checks  # noqa: E402
    from .rendering import (  # noqa: E402
        detect_scene_classes,
        render_scene,
    )


def _slugify(text: str, *, max_len: int = 48) -> str:
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^A-Za-z0-9_\\-\\u4e00-\\u9fff]+", "", s)
    s = s.strip("_")
    return (s[:max_len] or "run").strip("_")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_python_code(text: str) -> str:
    code = text.strip()
    if "```" in code:
        m = re.search(r"```(?:python)?\s*(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
        if m:
            code = m.group(1).strip()
    return code


def _normalize_manim_ce_api(code: str) -> str:
    """
    把常见旧版 manim API 规范化到 Manim CE 可用写法。
    这里先做保守替换，优先解决高频阻断项。
    """

    normalized = code
    normalized = re.sub(r"\bShowCreation\s*\(", "Create(", normalized)
    return normalized


def _safe_name(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(text).strip())
    value = value.strip("._-")
    return value or "unknown"


def _write_global_llm4_error_log(
    *,
    layout: RunLayout,
    attempt: int,
    class_name: str,
    returncode: int,
    stderr: str,
    stdout: str,
) -> None:
    """
    把 llm4 渲染报错集中落盘到 MVP/error/，便于跨 run 汇总排查。
    """

    try:
        ERROR_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int((time.time() % 1) * 1000)
        run_tag = _safe_name(layout.run_dir.name)
        cls_tag = _safe_name(class_name)
        filename = f"{ts}_{ms:03d}_{run_tag}_{cls_tag}_attempt{int(attempt)}.log"
        path = ERROR_DIR / filename
        content = (
            f"time={ts}.{ms:03d}\n"
            f"run_dir={layout.run_dir}\n"
            f"scene_file={layout.llm4_scene_py}\n"
            f"class_name={class_name}\n"
            f"attempt={int(attempt)}\n"
            f"returncode={int(returncode)}\n"
            f"render_stderr_file={layout.render_stderr(attempt)}\n"
            f"render_stdout_file={layout.render_stdout(attempt)}\n\n"
            f"=== STDERR ===\n{stderr.strip()}\n\n"
            f"=== STDOUT ===\n{stdout.strip()}\n"
        )
        _write_text(path, content)
    except Exception:  # noqa: BLE001
        # 全局日志写入失败不阻断主流程
        pass


def build_client() -> LLMClient:
    # 复用 MVP/configs/llm.yaml 里的 stage 采样 profile
    stage_map = {
        "analyst": LLMStage(name="analyst", zhipu_stage="analyst", prompt_bundle="llm1_analyst"),
        "scene_planner": LLMStage(
            name="scene_planner",
            zhipu_stage="scene_planner",
            prompt_bundle="llm2_scene_planner",
        ),
        "scene_designer": LLMStage(
            name="scene_designer",
            zhipu_stage="scene_designer",
            prompt_bundle="llm3_scene_designer",
        ),
        "codegen": LLMStage(name="codegen", zhipu_stage="codegen", prompt_bundle="llm4_codegen"),
        "fixer": LLMStage(name="fixer", zhipu_stage="fixer", prompt_bundle="llm5_fixer"),
    }
    return LLMClient(prompts_dir=PROMPTS_DIR, stage_map=stage_map)


def stage_analyst(client: LLMClient, *, requirement: str, out_dir: Path) -> dict[str, Any]:
    system = client.load_stage_system_prompt("analyst")
    user = requirement.strip()
    data, raw = client.generate_json(stage_key="analyst", system_prompt=system, user_prompt=user)
    _write_text(out_dir / "stage1_analyst_raw.txt", raw)
    client.save_json(out_dir / "stage1_analyst.json", data)
    return data


def stage_scene_plan(
    client: LLMClient, *, requirement: str, analyst: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    system = client.load_stage_system_prompt("scene_planner")
    user = (
        "【用户需求】\n"
        f"{requirement.strip()}\n\n"
        "【分析与前置探索 JSON】\n"
        f"{json.dumps(analyst, ensure_ascii=False, indent=2)}\n"
    )
    data, raw = client.generate_json(stage_key="scene_planner", system_prompt=system, user_prompt=user)
    _write_text(out_dir / "stage2_scene_plan_raw.txt", raw)

    # 轻量补全：保证 scenes 可用（避免后续因为字段缺失直接崩）
    total_s = analyst.get("total_duration_s")
    try:
        total_s_num = float(total_s) if total_s is not None else 120.0
    except Exception:  # noqa: BLE001
        total_s_num = 120.0

    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        scenes = []

    normalized: list[dict[str, Any]] = []
    for idx, sc in enumerate(scenes, start=1):
        if not isinstance(sc, dict):
            continue
        scene_id = str(sc.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        class_name = str(sc.get("class_name") or "").strip() or f"Scene{idx:02d}"
        title = str(sc.get("title") or "").strip() or scene_id
        goal = str(sc.get("goal") or "").strip()
        key_points = sc.get("key_points")
        if not isinstance(key_points, list):
            key_points = []
        duration_s = sc.get("duration_s")
        try:
            duration_num = float(duration_s) if duration_s is not None else 0.0
        except Exception:  # noqa: BLE001
            duration_num = 0.0

        # 额外字段（可选）：用于后续做“单文件串联”时的连贯性与聚合规划
        concepts = sc.get("concepts")
        if not isinstance(concepts, list):
            concepts = []

        importance = str(sc.get("importance") or "").strip().lower()
        if importance not in {"core", "supporting"}:
            importance = ""

        transition_in = str(sc.get("transition_in") or "").strip()
        transition_out = str(sc.get("transition_out") or "").strip()

        carry_over = sc.get("carry_over")
        if not isinstance(carry_over, list):
            carry_over = []

        normalized.append(
            {
                "scene_id": scene_id,
                "class_name": class_name,
                "title": title,
                "goal": goal,
                "key_points": [str(x) for x in key_points if str(x).strip()],
                "duration_s": duration_num,
                "concepts": [str(x) for x in concepts if str(x).strip()],
                "importance": importance,
                "transition_in": transition_in,
                "transition_out": transition_out,
                "carry_over": [str(x) for x in carry_over if str(x).strip()],
            }
        )

    if normalized:
        # 若模型没分配时长，按总时长均分一个兜底
        if sum(sc.get("duration_s", 0.0) for sc in normalized) <= 1e-6:
            per = max(5.0, total_s_num / len(normalized))
            for sc in normalized:
                sc["duration_s"] = round(per, 2)
        data["scenes"] = normalized

    client.save_json(out_dir / "stage2_scene_plan.json", data)
    return data


def stage_scene_design(
    client: LLMClient,
    *,
    requirement: str,
    analyst: dict[str, Any],
    scene: dict[str, Any],
    scene_dir: Path,
) -> dict[str, Any]:
    system = client.load_stage_system_prompt("scene_designer")
    user = (
        "【用户需求】\n"
        f"{requirement.strip()}\n\n"
        "【全局分析 JSON】\n"
        f"{json.dumps(analyst, ensure_ascii=False, indent=2)}\n\n"
        "【当前 Scene】\n"
        f"{json.dumps(scene, ensure_ascii=False, indent=2)}\n"
    )
    data, raw = client.generate_json(stage_key="scene_designer", system_prompt=system, user_prompt=user)
    _write_text(scene_dir / "design_raw.txt", raw)

    # 强制对齐 scene_id / class_name（避免后续 codegen 与渲染找不到类）
    expected_scene_id = str(scene.get("scene_id") or "").strip()
    expected_class = str(scene.get("class_name") or "").strip()
    if expected_scene_id:
        data["scene_id"] = expected_scene_id
    if expected_class:
        data["class_name"] = expected_class

    client.save_json(scene_dir / "design.json", data)
    return data


def stage_codegen(
    client: LLMClient,
    *,
    scene_design: dict[str, Any],
    scene_dir: Path,
) -> tuple[str, str]:
    system = client.load_stage_system_prompt("codegen")
    user = json.dumps(scene_design, ensure_ascii=False, indent=2)
    merged, raw, chunks = client.generate_code(
        stage_key="codegen",
        system_prompt=system,
        user_prompt=user,
        max_continue_rounds=3,
    )
    _write_text(scene_dir / "codegen_raw.txt", raw)
    for idx, chunk in enumerate(chunks, start=1):
        _write_text(scene_dir / f"codegen_continue_{idx}.txt", chunk)
    code = _normalize_manim_ce_api(_extract_python_code(merged))

    classes = detect_scene_classes(code)
    class_name = str(scene_design.get("class_name") or "").strip()
    if class_name and class_name not in classes and classes:
        # 兜底：如果模型没按约定类名输出，取第一个 Scene 子类名
        class_name = classes[0]
    if not class_name:
        class_name = classes[0] if classes else "GeneratedScene"
    return class_name, code + "\n"


def generate_scene_design(
    client: LLMClient,
    *,
    requirement: str,
    analyst: dict[str, Any],
    scene: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """
    为单个 scene 生成“分镜级设计稿”。
    返回：(design_json, raw_text)
    """

    system = client.load_stage_system_prompt("scene_designer")
    user = (
        "【用户需求】\n"
        f"{requirement.strip()}\n\n"
        "【全局分析 JSON】\n"
        f"{json.dumps(analyst, ensure_ascii=False, indent=2)}\n\n"
        "【当前 Scene（来自 Scene Planner）】\n"
        f"{json.dumps(scene, ensure_ascii=False, indent=2)}\n"
    )
    data, raw = client.generate_json(stage_key="scene_designer", system_prompt=system, user_prompt=user)

    # 强制对齐 scene_id / class_name（避免后续 codegen/渲染找不到类）
    expected_scene_id = str(scene.get("scene_id") or "").strip()
    expected_class = str(scene.get("class_name") or "").strip()
    if expected_scene_id:
        data["scene_id"] = expected_scene_id
    if expected_class:
        data["class_name"] = expected_class

    # 把规划信息也带上，方便后续“单文件”代码生成整合
    for key in ("title", "goal", "key_points", "duration_s"):
        if key in scene and key not in data:
            data[key] = scene.get(key)

    return data, raw


def stage_scene_designs(
    client: LLMClient,
    *,
    requirement: str,
    analyst: dict[str, Any],
    plan: dict[str, Any],
    out_dir: Path,
    scene_id: str = "",
) -> dict[str, Any]:
    """
    逐 scene 生成设计稿，但把结果聚合到一个 JSON 文件里：
    - stage3_scene_designs.json
    - stage3_<scene_id>_raw.txt（便于排查某个 scene 的输出）
    """

    scenes = plan.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("stage2_scene_plan.json 中缺少 scenes 列表")

    wanted = scene_id.strip()
    if wanted:
        scenes = [sc for sc in scenes if isinstance(sc, dict) and str(sc.get("scene_id") or "").strip() == wanted]
        if not scenes:
            raise RuntimeError(f"未找到 scene_id={wanted}（请检查 stage2_scene_plan.json）")
    else:
        scenes = [sc for sc in scenes if isinstance(sc, dict)]

    designs: list[dict[str, Any]] = []
    for sc in scenes:
        sid = str(sc.get("scene_id") or "").strip() or "scene_unknown"
        design, raw = generate_scene_design(
            client,
            requirement=requirement,
            analyst=analyst,
            scene=sc,
        )
        _write_text(out_dir / f"stage3_{sid}_raw.txt", raw)
        designs.append(design)

    payload = {
        "video_title": str(plan.get("video_title") or "").strip(),
        "scenes": designs,
    }
    client.save_json(out_dir / "stage3_scene_designs.json", payload)
    return payload


def stage_codegen_video(
    client: LLMClient,
    *,
    analyst: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    out_dir: Path,
) -> tuple[str, str]:
    """
    把多个 scene 的设计稿整合成一个可直接运行的单文件：scene.py（单一 Scene 类）。
    返回：(class_name, code)
    """

    system = client.load_stage_system_prompt("codegen")
    user_payload = {
        "analyst": analyst,
        "scene_plan": plan,
        "scene_designs": scene_designs,
        "output_contract": {
            "single_file": True,
            "preferred_class_name": "MainScene",
            "file_name": "scene.py",
        },
    }
    user = json.dumps(user_payload, ensure_ascii=False, indent=2)
    merged, raw, chunks = client.generate_code(
        stage_key="codegen",
        system_prompt=system,
        user_prompt=user,
        max_continue_rounds=4,
    )
    _write_text(out_dir / "stage4_codegen_raw.txt", raw)
    for idx, chunk in enumerate(chunks, start=1):
        _write_text(out_dir / f"stage4_codegen_continue_{idx}.txt", chunk)

    code = _normalize_manim_ce_api(_extract_python_code(merged))

    classes = detect_scene_classes(code)
    class_name = "MainScene"
    if classes and class_name not in classes:
        # 兜底：如果模型没按约定输出 MainScene，则用第一个 Scene 子类名渲染
        class_name = classes[0]
    if not classes:
        class_name = "MainScene"

    return class_name, code + "\n"


def stage_fix_code(
    client: LLMClient,
    *,
    class_name: str,
    code: str,
    stderr: str,
    scene_dir: Path,
    attempt: int,
) -> str:
    system = client.load_stage_system_prompt("fixer")
    user = (
        f"【目标类名】{class_name}\n\n"
        f"【第 {attempt} 轮错误日志】\n{stderr}\n\n"
        f"【当前代码】\n{code}\n"
    )
    merged, raw, chunks = client.generate_code(
        stage_key="fixer",
        mode="repair",
        system_prompt=system,
        user_prompt=user,
        max_continue_rounds=4,
    )
    _write_text(scene_dir / f"fix_raw_{attempt}.txt", raw)
    for idx, chunk in enumerate(chunks, start=1):
        _write_text(scene_dir / f"fix_continue_{attempt}_{idx}.txt", chunk)
    fixed = _normalize_manim_ce_api(_extract_python_code(merged))
    return fixed + "\n"


def stage_static_gate(
    client: LLMClient,
    *,
    class_name: str,
    py_file: Path,
    layout: RunLayout,
    max_rounds: int = 3,
    attempt_base: int = 1000,
) -> tuple[str, bool, str, int]:
    """
    静态闸门：先跑 py_compile + pyflakes。
    - 通过：返回 (class_name, True, report)
    - 不通过：调用 Fixer 自动修复，最多 max_rounds 轮
    """

    rounds = max(0, int(max_rounds))
    last_report = ""

    for idx in range(rounds + 1):
        check = run_static_checks(py_file)
        last_report = check.to_report()
        _write_text(layout.llm5_dir / f"static_check_{idx}.txt", last_report)

        if check.ok:
            return class_name, True, last_report, idx

        if idx >= rounds:
            return class_name, False, last_report, idx

        _write_text(layout.llm5_system_prompt, client.load_stage_system_prompt("fixer").strip() + "\n")
        fixed = stage_fix_code(
            client,
            class_name=class_name,
            code=py_file.read_text(encoding="utf-8"),
            stderr=last_report,
            scene_dir=layout.llm5_dir,
            attempt=attempt_base + idx + 1,
        )
        _write_text(py_file, fixed)
        _write_text(layout.exported_scene_py, fixed)

        classes = detect_scene_classes(fixed)
        if classes and class_name not in classes:
            class_name = classes[0]

        _write_text(
            layout.stage4_meta,
            json.dumps(
                {"class_name": class_name, "last_static_fix_round": idx + 1},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

    return class_name, False, last_report, rounds


def stage_render_fix_loop(
    client: LLMClient,
    *,
    class_name: str,
    py_file: Path,
    layout: RunLayout,
    quality: str = "l",
    render_timeout_s: int = 300,
    max_fix_rounds: int = 5,
) -> tuple[str, bool, Path | None, str, int]:
    """
    渲染失败驱动修复循环：
    - 先直接执行 manim 渲染
    - 失败则把完整日志交给 Fixer（LLM5）修复
    - 修复后再次渲染，直到成功或达到最大轮数
    """

    media_dir = layout.render_media_dir
    rounds = max(0, int(max_fix_rounds))
    last_err = ""

    for attempt in range(0, rounds + 1):
        print(f"[MVP] 渲染尝试 {attempt} ...")
        result = render_scene(
            py_file=py_file,
            class_name=class_name,
            media_dir=media_dir,
            quality=quality,  # type: ignore[arg-type]
            timeout_s=int(render_timeout_s),
        )
        _write_text(layout.render_stdout(attempt), result.stdout)
        _write_text(layout.render_stderr(attempt), result.stderr)

        if result.ok and result.mp4_path:
            final_mp4 = layout.render_final_mp4
            try:
                shutil.copyfile(result.mp4_path, final_mp4)
                shutil.copyfile(final_mp4, layout.exported_final_mp4)
            except Exception:  # noqa: BLE001
                pass
            return class_name, True, result.mp4_path, "", attempt

        last_err = (
            f"[manim returncode] {result.returncode}\n\n"
            f"【stderr】\n{(result.stderr or '').strip() or '<empty>'}\n\n"
            f"【stdout】\n{(result.stdout or '').strip() or '<empty>'}\n"
        )
        _write_text(layout.llm5_dir / f"render_error_{attempt}.txt", last_err)
        _write_global_llm4_error_log(
            layout=layout,
            attempt=attempt,
            class_name=class_name,
            returncode=result.returncode,
            stderr=result.stderr or "",
            stdout=result.stdout or "",
        )

        if attempt >= rounds:
            return class_name, False, None, last_err, attempt

        print("[MVP] 进入修复（Fixer） ...")
        _write_text(layout.llm5_system_prompt, client.load_stage_system_prompt("fixer").strip() + "\n")
        fixed = stage_fix_code(
            client,
            class_name=class_name,
            code=py_file.read_text(encoding="utf-8"),
            stderr=last_err,
            scene_dir=layout.llm5_dir,
            attempt=attempt + 1,
        )
        _write_text(py_file, fixed)
        _write_text(layout.exported_scene_py, fixed)

        classes = detect_scene_classes(fixed)
        if classes and class_name not in classes:
            class_name = classes[0]

        _write_text(
            layout.stage4_meta,
            json.dumps(
                {
                    "class_name": class_name,
                    "last_fix_attempt": attempt + 1,
                    "last_render_returncode": result.returncode,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

    return class_name, False, None, last_err, rounds


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MVP: 多 LLM 分工 -> 最终生成单个 scene.py（优先可运行）")
    p.add_argument("-r", "--requirement", type=str, default="")
    p.add_argument("--requirement-file", type=str, default="")
    p.add_argument("--run-dir", type=str, default="")
    p.add_argument("--quality", choices=["l", "m", "h"], default="l", help="manim 渲染质量：l 最快")
    p.add_argument("--render-timeout-s", type=int, default=300, help="单个渲染任务超时（秒）")
    p.add_argument("--max-fix-rounds", type=int, default=5)
    p.add_argument("--max-static-fix-rounds", type=int, default=3, help="已废弃参数（兼容保留，不再使用）")
    p.add_argument("--no-render", action="store_true", help="只生成代码，不执行 manim 渲染")
    return p.parse_args()


def _read_requirement(args: argparse.Namespace) -> str:
    if args.requirement:
        return args.requirement.strip()
    if args.requirement_file:
        return Path(args.requirement_file).read_text(encoding="utf-8").strip()

    # 兼容：如果指定了 run_dir 且其中已有 requirement.txt，则复用
    if args.run_dir:
        req_path = Path(args.run_dir) / "requirement.txt"
        if req_path.exists():
            return req_path.read_text(encoding="utf-8").strip()

    raise SystemExit("requirement 为空：请用 -r 或 --requirement-file 提供，或指定含 requirement.txt 的 --run-dir。")


def main() -> int:
    args = parse_args()
    requirement = _read_requirement(args)

    run_id = time.strftime("%Y%m%d_%H%M%S")
    slug = _slugify(requirement)

    # Case 约定：如果 requirement-file 来自 MVP/cases/<case_name>/problem.txt，且未显式指定 --run-dir，
    # 则默认把产物落在 case 目录下（再按 llm1..llm5/render 分文件夹）。
    inferred: Path | None = None
    if not args.run_dir and args.requirement_file:
        try:
            req_path = Path(args.requirement_file).resolve()
            cases_root = (RUNS_DIR.parent / "cases").resolve()
            rel = req_path.relative_to(cases_root)
            if len(rel.parts) >= 2:
                inferred = cases_root / rel.parts[0]
        except Exception:  # noqa: BLE001
            inferred = None

    run_dir = Path(args.run_dir) if args.run_dir else (inferred or (RUNS_DIR / f"{run_id}_{slug}"))
    run_dir.mkdir(parents=True, exist_ok=True)
    layout = RunLayout.from_run_dir(run_dir)

    print(f"[MVP] 运行目录: {run_dir}")
    _write_text(layout.requirement_txt, requirement + "\n")

    client = build_client()

    print("[MVP] Stage 1/4: 分析 + 前置探索 ...")
    _write_text(layout.llm1_system_prompt, client.load_stage_system_prompt("analyst").strip() + "\n")
    analyst = stage_analyst(client, requirement=requirement, out_dir=layout.llm1_dir)
    print("[MVP] Stage 2/4: Scene 拆分规划 ...")
    _write_text(layout.llm2_system_prompt, client.load_stage_system_prompt("scene_planner").strip() + "\n")
    plan = stage_scene_plan(client, requirement=requirement, analyst=analyst, out_dir=layout.llm2_dir)
    print("[MVP] Stage 3/4: 逐 Scene 设计（分镜稿） ...")
    _write_text(layout.llm3_system_prompt, client.load_stage_system_prompt("scene_designer").strip() + "\n")
    scene_designs = stage_scene_designs(
        client,
        requirement=requirement,
        analyst=analyst,
        plan=plan,
        out_dir=layout.llm3_dir,
    )
    print(f"[MVP] 已输出: {layout.stage3_json}")
    print("[MVP] Stage 4/4: 单文件代码生成（scene.py） ...")
    _write_text(layout.llm4_system_prompt, client.load_stage_system_prompt("codegen").strip() + "\n")
    class_name, code = stage_codegen_video(
        client,
        analyst=analyst,
        plan=plan,
        scene_designs=scene_designs,
        out_dir=layout.llm4_dir,
    )

    py_file = layout.llm4_scene_py
    _write_text(py_file, code)
    # 导出到 run_dir 根目录，方便直接运行
    _write_text(layout.exported_scene_py, code)
    _write_text(
        layout.stage4_meta,
        json.dumps({"class_name": class_name}, ensure_ascii=False, indent=2) + "\n",
    )
    print(f"[MVP] 已生成: {py_file}（class_name={class_name}）")

    if args.no_render:
        return 0

    print("[MVP] 开始执行：渲染失败驱动修复循环（LLM4 -> manim -> LLM5 -> 重试）")
    class_name, ok, mp4_path, last_err, _last_attempt = stage_render_fix_loop(
        client,
        class_name=class_name,
        py_file=py_file,
        layout=layout,
        quality=args.quality,
        render_timeout_s=int(args.render_timeout_s),
        max_fix_rounds=int(args.max_fix_rounds),
    )
    if ok:
        print(f"[MVP] 渲染成功 -> {mp4_path}")
        return 0

    print("[MVP] 渲染失败（达到最大修复轮数）")
    _write_text(run_dir / "FAILED.txt", f"渲染失败：达到最大修复轮数 {args.max_fix_rounds}\n\n{last_err}")
    return 5


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise
