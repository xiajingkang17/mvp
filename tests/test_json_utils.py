from __future__ import annotations

import json

import pytest

from pipeline.json_utils import extract_first_json, load_json_from_llm


def test_extract_first_json_object():
    text = "前缀说明\n```json\n{\"a\": 1, \"b\": 2}\n```\n后缀"
    assert extract_first_json(text) == "{\"a\": 1, \"b\": 2}"


def test_load_json_from_llm_fallback_extracts():
    text = "解释一下：\n{\"x\": 3}\n"
    assert load_json_from_llm(text) == {"x": 3}


def test_extract_first_json_raises_when_missing():
    with pytest.raises(ValueError):
        extract_first_json("没有 JSON")

