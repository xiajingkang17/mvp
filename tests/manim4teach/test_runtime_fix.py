from __future__ import annotations

import shutil
from pathlib import Path

from Manim4Teach.pipeline.stage2.runtime_fix import run_runtime_fix_loop, summarize_runtime_error
from Manim4Teach.pipeline.stage2.static_checks import run_static_checks


class _FakeClient:
    def load_stage_system_prompt(self, stage_key: str) -> str:
        assert stage_key == "runtime_fix"
        return "system"

    def chat(self, *, stage_key: str, mode: str, system_prompt: str, user_prompt: str) -> str:
        assert stage_key == "runtime_fix"
        assert mode == "generate"
        assert "missing_obj" in user_prompt
        return (
            "from manim import *\n\n"
            "class GeneratedTeachScene(Scene):\n"
            "    def construct(self):\n"
            "        title = Text('test')\n"
            "        self.play(Write(title))\n"
            "        self.wait(1)\n"
        )


def _fake_preview_render(*, scene_path: Path, class_name: str, out_dir: Path, round_index: int, write_report_path: Path | None = None):
    code = scene_path.read_text(encoding="utf-8")
    ok = "missing_obj" not in code
    report = {
        "ok": ok,
        "round_index": round_index,
        "scene_path": str(scene_path),
        "class_name": class_name,
        "render": {
            "returncode": 0 if ok else 1,
            "cmd": ["python", "-m", "manim"],
            "stdout_tail": "",
            "stderr_tail": "" if ok else "NameError: name 'missing_obj' is not defined",
        },
        "artifacts": {
            "video": "",
            "duration_seconds": 6.0 if ok else 0.0,
            "keyframes": [],
            "clips": [],
        },
    }
    if write_report_path is not None:
        write_report_path.parent.mkdir(parents=True, exist_ok=True)
        write_report_path.write_text("{}", encoding="utf-8")
    return report


def test_summarize_runtime_error_extracts_name_error() -> None:
    summary = summarize_runtime_error(
        static_report={"compile_ok": True, "compile_error": ""},
        preview_report={
            "ok": False,
            "render": {
                "stdout_tail": "",
                "stderr_tail": "Traceback...\nNameError: name 'missing_obj' is not defined\n",
            },
        },
    )
    assert summary["error_type"] == "NameError"
    assert "missing_obj" in summary["error_message"]


def test_runtime_summary_prefers_specific_error_over_traceback() -> None:
    summary = summarize_runtime_error(
        static_report={"compile_ok": True, "compile_error": ""},
        preview_report={
            "ok": False,
            "render": {
                "stdout_tail": "",
                "stderr_tail": (
                    "Traceback (most recent call last):\n"
                    '  File "scene.py", line 8, in construct\n'
                    "TypeError: VGroup expected VMobject entries\n"
                ),
            },
        },
    )
    assert summary["runtime_summary"] == "TypeError: VGroup expected VMobject entries"
    assert summary["error_type"] == "TypeError"


def test_runtime_fix_loop_repairs_failed_preview() -> None:
    tmp_dir = Path("Manim4Teach") / "runs" / "_tmp_runtime_fix"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    scene_path = tmp_dir / "scene.py"
    scene_path.write_text(
        "\n".join(
            [
                "from manim import *",
                "",
                "class GeneratedTeachScene(Scene):",
                "    def construct(self):",
                "        title = Text('test')",
                "        self.play(Write(missing_obj))",
                "        self.wait(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    static_report = run_static_checks(scene_path)
    preview_report = _fake_preview_render(
        scene_path=scene_path,
        class_name="GeneratedTeachScene",
        out_dir=tmp_dir / "preview",
        round_index=1,
    )

    report = run_runtime_fix_loop(
        client=_FakeClient(),  # type: ignore[arg-type]
        requirement="生成一段可渲染的讲解动画",
        analysis_packet={"mode": "problem", "problem_solving": {"problem_statement": "test"}},
        scene_path=scene_path,
        class_name="GeneratedTeachScene",
        static_report=static_report,
        preview_report=preview_report,
        out_dir=tmp_dir / "runtime_fix",
        round_index=1,
        max_attempts=2,
        render_fn=_fake_preview_render,
    )

    assert report["status"] == "fixed"
    assert report["fixed"] is True
    assert report["attempt_count"] == 1
    assert report["preview_report"]["ok"] is True
    fixed_scene = Path(report["scene_path"])
    assert fixed_scene.exists()
    assert "missing_obj" not in fixed_scene.read_text(encoding="utf-8")

    shutil.rmtree(tmp_dir, ignore_errors=True)
