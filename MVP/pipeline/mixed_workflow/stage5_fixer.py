from __future__ import annotations

from .common import (
    LLMClient,
    Path,
    RunLayout,
    _extract_python_code,
    _normalize_manim_ce_api,
    _write_global_llm4_error_log,
    _write_text,
    detect_scene_classes,
    json,
    render_scene,
    shutil,
)

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


