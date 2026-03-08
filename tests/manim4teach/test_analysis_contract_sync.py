from __future__ import annotations

import json
from pathlib import Path

import pytest

from Manim4Teach.pipeline.stage1.analysis_contract import (
    MIN_ANSWER_CHECK_ITEMS,
    MIN_KNOWN_CONDITIONS,
    MIN_KNOWLEDGE_TREE_EDGES,
    MIN_KNOWLEDGE_TREE_NODES,
    MIN_PROBLEM_SOLVING_STEPS,
    MIN_STEP_EQUATIONS,
)
from Manim4Teach.pipeline.stage1.analysis_packet import AnalysisPacketError, normalize_analysis_packet


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "Manim4Teach" / "schema" / "analysis_packet.schema.json"
PROMPT_SYSTEM_PATH = ROOT / "Manim4Teach" / "prompts" / "llm1_analysis_packet" / "system.md"
PROMPT_OUTPUT_SCHEMA_PATH = ROOT / "Manim4Teach" / "prompts" / "llm1_analysis_packet" / "output_schema.md"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _problem_schema(schema: dict) -> dict:
    for item in schema.get("oneOf") or []:
        if item.get("title") == "ProblemPacket":
            return item
    raise AssertionError("schema 缺少 ProblemPacket")


def _concept_schema(schema: dict) -> dict:
    for item in schema.get("oneOf") or []:
        if item.get("title") == "ConceptPacket":
            return item
    raise AssertionError("schema 缺少 ConceptPacket")


def _build_problem_packet() -> dict:
    return {
        "mode": "problem",
        "problem_solving": {
            "is_problem_video": True,
            "problem_statement": "已知 x + y = 1，求 x^2 + y^2 的最小值",
            "known_conditions": ["x + y = 1"],
            "target_question": "求 x^2 + y^2 的最小值",
            "full_solution_steps": [
                {
                    "step": 1,
                    "goal": "使用恒等变形",
                    "reasoning": "利用 x^2+y^2=(x+y)^2-2xy",
                    "equations": ["x^2+y^2=(x+y)^2-2xy", "x+y=1"],
                    "result": "x^2+y^2=1-2xy",
                }
            ],
            "final_answer": "最小值为 1/2",
            "answer_check": ["当 x=y=1/2 时取到最小值 1/2"],
        },
    }


def _build_concept_packet(node_count: int, edge_count: int) -> dict:
    nodes = [
        {
            "node_id": "target",
            "concept": "拉格朗日乘子法",
            "type": "target",
        }
    ]
    for idx in range(max(0, node_count - 1)):
        nodes.append(
            {
                "node_id": f"p{idx+1}",
                "concept": f"前置概念{idx+1}",
                "type": "prerequisite",
            }
        )

    edges = []
    for idx in range(edge_count):
        src = f"p{(idx % max(1, node_count - 1)) + 1}" if node_count > 1 else "target"
        edges.append(
            {
                "from": src,
                "to": "target",
                "relation": "prerequisite",
            }
        )

    return {
        "mode": "concept",
        "knowledge_tree": {
            "target_concept": "拉格朗日乘子法",
            "nodes": nodes,
            "edges": edges,
        },
    }


def test_schema_matches_contract_constants() -> None:
    schema = _load_schema()
    problem = _problem_schema(schema)
    concept = _concept_schema(schema)

    solving = problem["properties"]["problem_solving"]["properties"]
    assert solving["known_conditions"]["minItems"] == MIN_KNOWN_CONDITIONS
    assert solving["full_solution_steps"]["minItems"] == MIN_PROBLEM_SOLVING_STEPS
    step_props = solving["full_solution_steps"]["items"]["properties"]
    assert step_props["equations"]["minItems"] == MIN_STEP_EQUATIONS
    assert solving["answer_check"]["minItems"] == MIN_ANSWER_CHECK_ITEMS

    concept_tree = concept["properties"]["knowledge_tree"]["properties"]
    assert concept_tree["nodes"]["minItems"] == MIN_KNOWLEDGE_TREE_NODES
    assert concept_tree["edges"]["minItems"] == MIN_KNOWLEDGE_TREE_EDGES


def test_validator_behavior_matches_schema() -> None:
    valid_problem = _build_problem_packet()
    assert normalize_analysis_packet(valid_problem)["mode"] == "problem"

    with pytest.raises(AnalysisPacketError):
        packet = _build_problem_packet()
        packet["problem_solving"]["problem_statement"] = "   "
        normalize_analysis_packet(packet)

    with pytest.raises(AnalysisPacketError):
        packet = _build_problem_packet()
        packet["problem_solving"]["is_problem_video"] = False
        normalize_analysis_packet(packet)

    with pytest.raises(AnalysisPacketError):
        packet = _build_problem_packet()
        packet["problem_solving"]["full_solution_steps"][0]["equations"] = []
        normalize_analysis_packet(packet)

    valid_concept = _build_concept_packet(
        node_count=MIN_KNOWLEDGE_TREE_NODES,
        edge_count=MIN_KNOWLEDGE_TREE_EDGES,
    )
    assert normalize_analysis_packet(valid_concept)["mode"] == "concept"

    with pytest.raises(AnalysisPacketError):
        normalize_analysis_packet(_build_concept_packet(node_count=MIN_KNOWLEDGE_TREE_NODES - 1, edge_count=1))

    with pytest.raises(AnalysisPacketError):
        normalize_analysis_packet(_build_concept_packet(node_count=2, edge_count=MIN_KNOWLEDGE_TREE_EDGES - 1))


def test_prompt_mentions_only_two_payload_modes() -> None:
    system_text = PROMPT_SYSTEM_PATH.read_text(encoding="utf-8")
    output_schema_text = PROMPT_OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8")

    assert "problem_solving" in system_text
    assert "只输出知识树" in system_text

    assert "\"problem_solving\"" in output_schema_text
    assert "concept 模式（只输出知识树）" in output_schema_text
