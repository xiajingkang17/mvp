from __future__ import annotations

from pipeline.run_llm2 import _compact_teaching_plan


def test_compact_teaching_plan_keeps_scene_packet_focus():
    plan = {
        "global_symbols": [{"name": "m", "meaning": "质量"}],
        "sub_questions": [
            {
                "id": "Q1",
                "goal": "求速度",
                "given_conditions": ["条件1"],
                "method_choice": {"method": "energy", "reason": "理由"},
                "result": {"expression": "v=1"},
                "sanity_checks": ["单位检查"],
                "scene_packets": [
                    {"content_items": ["diagram", "goal"], "primary_item": "diagram"},
                ],
            }
        ],
    }
    compact = _compact_teaching_plan(plan)
    assert compact is not None
    assert compact["sub_questions"][0]["scene_packets"][0]["primary_item"] == "diagram"

