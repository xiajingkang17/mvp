from __future__ import annotations

import shutil
from pathlib import Path

from Manim4Teach.pipeline.stage2.review_rules import run_rule_review
from Manim4Teach.pipeline.stage2.static_checks import run_static_checks


def test_stage2_static_and_rule_review_smoke() -> None:
    tmp_dir = Path("Manim4Teach") / "runs" / "_tmp_stage2_smoke"
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
                "        title = Text('测试')",
                "        self.add(title)",
                "        self.wait(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    static_report = run_static_checks(scene_path)
    assert static_report["compile_ok"] is True
    assert "metrics" in static_report

    rule_report = run_rule_review(static_report=static_report, preview_report=None)
    assert isinstance(rule_report.get("issues"), list)
    assert rule_report.get("should_revise") is True

    shutil.rmtree(tmp_dir, ignore_errors=True)
