from __future__ import annotations

import os
from pathlib import Path

from pipeline.env import load_dotenv


def test_load_dotenv_reads_key_value(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# 注释",
                "ZHIPUAI_API_KEY=abc123",
                "export ZHIPU_MODEL=glm-4.7",
                "EMPTY=",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("ZHIPUAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_MODEL", raising=False)

    assert load_dotenv(env_file) is True
    assert os.environ["ZHIPUAI_API_KEY"] == "abc123"
    assert os.environ["ZHIPU_MODEL"] == "glm-4.7"

