from __future__ import annotations

import shutil
from pathlib import Path

from Manim4Teach.pipeline.core.question_parser import parse_question_text


def test_parse_question_text_extracts_images_and_keeps_text() -> None:
    tmp_path = Path("Manim4Teach") / "runs" / "_tmp_question_parser"
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)

    img_a = tmp_path / "a.png"
    img_b = tmp_path / "b.jpg"
    img_a.write_bytes(b"\x89PNG\r\n\x1a\n")
    img_b.write_bytes(b"\xff\xd8\xff")

    raw = "\n".join(
        [
            "已知如图，求最小值。",
            "图片: ./a.png",
            "请补充说明。",
            "![题图](./b.jpg)",
        ]
    )
    text, images = parse_question_text(raw, base_dir=tmp_path)

    assert "已知如图，求最小值。" in text
    assert "请补充说明。" in text
    assert "图片:" not in text
    assert "![" not in text
    assert images == [img_a.resolve(), img_b.resolve()]

    shutil.rmtree(tmp_path, ignore_errors=True)
