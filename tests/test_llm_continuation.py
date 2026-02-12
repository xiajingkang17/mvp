from __future__ import annotations

import json

import pipeline.llm_continuation as lc
from pipeline.json_utils import load_json_from_llm


def test_stitch_continuation_with_overlap():
    prefix = '{"a":1,"b":2,'
    continuation = '"b":2,"c":3}'
    merged = lc.stitch_continuation(prefix, continuation)
    assert merged == '{"a":1,"b":2,"c":3}'


def test_continue_json_output_can_finish_truncated_json(monkeypatch):
    chunks = iter([', "b": 2', "}"])

    def fake_chat_completion(_messages):
        return next(chunks)

    monkeypatch.setattr(lc, "chat_completion", fake_chat_completion)

    merged, cont_chunks = lc.continue_json_output(
        '{"a": 1',
        system_prompt="sys",
        user_payload="payload",
        parse_fn=load_json_from_llm,
        max_rounds=3,
    )

    assert len(cont_chunks) == 2
    assert json.loads(merged) == {"a": 1, "b": 2}


def test_is_incomplete_json_error():
    assert lc.is_incomplete_json_error(ValueError("JSON seems incomplete (missing closing bracket)."))
    assert lc.is_incomplete_json_error(ValueError("Unterminated string starting at"))
    assert not lc.is_incomplete_json_error(ValueError("Extra data"))
