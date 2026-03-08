from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .analysis_contract import (
    EDGE_RELATIONS,
    MIN_ANSWER_CHECK_ITEMS,
    MIN_KNOWN_CONDITIONS,
    MIN_KNOWLEDGE_TREE_EDGES,
    MIN_KNOWLEDGE_TREE_NODES,
    MIN_PROBLEM_SOLVING_STEPS,
    MIN_STEP_EQUATIONS,
    NODE_TYPES,
)


class AnalysisPacketError(ValueError):
    """analysis_packet 结构不合法时抛出。"""


def _normalize_non_empty_str(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AnalysisPacketError(f"{field} 必须是非空字符串")
    return text


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AnalysisPacketError(f"{field} 必须是对象")
    return value


def _reject_unknown_keys(obj: Mapping[str, Any], *, field: str, allowed: set[str]) -> None:
    unknown = sorted(set(obj.keys()) - allowed)
    if unknown:
        raise AnalysisPacketError(f"{field} 含有未允许字段: {unknown}")


def _normalize_non_empty_str_list(value: Any, *, field: str, min_items: int = 0) -> list[str]:
    if not isinstance(value, list):
        raise AnalysisPacketError(f"{field} 必须是数组")
    out: list[str] = []
    for idx, item in enumerate(value):
        out.append(_normalize_non_empty_str(item, field=f"{field}[{idx}]"))
    if len(out) < min_items:
        raise AnalysisPacketError(f"{field} 至少 {min_items} 项")
    return out


def _normalize_positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AnalysisPacketError(f"{field} 必须是正整数")
    if value < 1:
        raise AnalysisPacketError(f"{field} 必须 >= 1")
    return value


def _normalize_solution_step(value: Any, *, index: int) -> dict[str, Any]:
    field = f"problem_solving.full_solution_steps[{index}]"
    row = _require_mapping(value, field=field)
    _reject_unknown_keys(
        row,
        field=field,
        allowed={"step", "goal", "reasoning", "equations", "result"},
    )
    return {
        "step": _normalize_positive_int(row.get("step"), field=f"{field}.step"),
        "goal": _normalize_non_empty_str(row.get("goal"), field=f"{field}.goal"),
        "reasoning": _normalize_non_empty_str(row.get("reasoning"), field=f"{field}.reasoning"),
        "equations": _normalize_non_empty_str_list(
            row.get("equations"),
            field=f"{field}.equations",
            min_items=MIN_STEP_EQUATIONS,
        ),
        "result": _normalize_non_empty_str(row.get("result"), field=f"{field}.result"),
    }


def _normalize_problem_solving(value: Any) -> dict[str, Any]:
    row = _require_mapping(value, field="problem_solving")
    _reject_unknown_keys(
        row,
        field="problem_solving",
        allowed={
            "is_problem_video",
            "problem_statement",
            "known_conditions",
            "target_question",
            "full_solution_steps",
            "final_answer",
            "answer_check",
        },
    )
    if row.get("is_problem_video") is not True:
        raise AnalysisPacketError("problem_solving.is_problem_video 在 problem 模式下必须为 true")

    known_conditions = _normalize_non_empty_str_list(
        row.get("known_conditions"),
        field="problem_solving.known_conditions",
        min_items=MIN_KNOWN_CONDITIONS,
    )
    steps_raw = row.get("full_solution_steps")
    if not isinstance(steps_raw, list):
        raise AnalysisPacketError("problem_solving.full_solution_steps 必须是数组")
    steps = [_normalize_solution_step(item, index=idx) for idx, item in enumerate(steps_raw)]
    if len(steps) < MIN_PROBLEM_SOLVING_STEPS:
        raise AnalysisPacketError(f"problem_solving.full_solution_steps 至少 {MIN_PROBLEM_SOLVING_STEPS} 项")

    answer_check = _normalize_non_empty_str_list(
        row.get("answer_check"),
        field="problem_solving.answer_check",
        min_items=MIN_ANSWER_CHECK_ITEMS,
    )

    return {
        "is_problem_video": True,
        "problem_statement": _normalize_non_empty_str(
            row.get("problem_statement"),
            field="problem_solving.problem_statement",
        ),
        "known_conditions": known_conditions,
        "target_question": _normalize_non_empty_str(
            row.get("target_question"),
            field="problem_solving.target_question",
        ),
        "full_solution_steps": steps,
        "final_answer": _normalize_non_empty_str(
            row.get("final_answer"),
            field="problem_solving.final_answer",
        ),
        "answer_check": answer_check,
    }


def _normalize_knowledge_tree(value: Any) -> dict[str, Any]:
    row = _require_mapping(value, field="knowledge_tree")
    _reject_unknown_keys(
        row,
        field="knowledge_tree",
        allowed={"target_concept", "nodes", "edges"},
    )

    nodes_raw = row.get("nodes")
    if not isinstance(nodes_raw, list):
        raise AnalysisPacketError("knowledge_tree.nodes 必须是数组")
    nodes: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(nodes_raw):
        node = _require_mapping(item, field=f"knowledge_tree.nodes[{idx}]")
        _reject_unknown_keys(
            node,
            field=f"knowledge_tree.nodes[{idx}]",
            allowed={"node_id", "concept", "type"},
        )
        node_id = _normalize_non_empty_str(node.get("node_id"), field=f"knowledge_tree.nodes[{idx}].node_id")
        if node_id in seen_ids:
            raise AnalysisPacketError(f"knowledge_tree.nodes[{idx}].node_id 重复: {node_id}")
        seen_ids.add(node_id)

        node_type = _normalize_non_empty_str(node.get("type"), field=f"knowledge_tree.nodes[{idx}].type")
        if node_type not in NODE_TYPES:
            raise AnalysisPacketError(f"knowledge_tree.nodes[{idx}].type 仅允许 {sorted(NODE_TYPES)}")

        nodes.append(
            {
                "node_id": node_id,
                "concept": _normalize_non_empty_str(node.get("concept"), field=f"knowledge_tree.nodes[{idx}].concept"),
                "type": node_type,
            }
        )
    if len(nodes) < MIN_KNOWLEDGE_TREE_NODES:
        raise AnalysisPacketError(f"knowledge_tree.nodes 至少 {MIN_KNOWLEDGE_TREE_NODES} 项")

    edges_raw = row.get("edges")
    if not isinstance(edges_raw, list):
        raise AnalysisPacketError("knowledge_tree.edges 必须是数组")
    edges: list[dict[str, str]] = []
    for idx, item in enumerate(edges_raw):
        edge = _require_mapping(item, field=f"knowledge_tree.edges[{idx}]")
        _reject_unknown_keys(
            edge,
            field=f"knowledge_tree.edges[{idx}]",
            allowed={"from", "to", "relation"},
        )
        frm = _normalize_non_empty_str(edge.get("from"), field=f"knowledge_tree.edges[{idx}].from")
        to = _normalize_non_empty_str(edge.get("to"), field=f"knowledge_tree.edges[{idx}].to")
        if frm not in seen_ids or to not in seen_ids:
            raise AnalysisPacketError(f"knowledge_tree.edges[{idx}] 引用了不存在的 node_id")

        relation = _normalize_non_empty_str(edge.get("relation"), field=f"knowledge_tree.edges[{idx}].relation")
        if relation not in EDGE_RELATIONS:
            raise AnalysisPacketError(f"knowledge_tree.edges[{idx}].relation 仅允许 {sorted(EDGE_RELATIONS)}")

        edges.append({"from": frm, "to": to, "relation": relation})
    if len(edges) < MIN_KNOWLEDGE_TREE_EDGES:
        raise AnalysisPacketError(f"knowledge_tree.edges 至少 {MIN_KNOWLEDGE_TREE_EDGES} 项")

    return {
        "target_concept": _normalize_non_empty_str(row.get("target_concept"), field="knowledge_tree.target_concept"),
        "nodes": nodes,
        "edges": edges,
    }


def normalize_analysis_packet(payload: Mapping[str, Any]) -> dict[str, Any]:
    row = _require_mapping(payload, field="analysis_packet")
    mode = _normalize_non_empty_str(row.get("mode"), field="mode").lower()

    if mode == "problem":
        _reject_unknown_keys(
            row,
            field="analysis_packet",
            allowed={"mode", "problem_solving"},
        )
        return {
            "mode": "problem",
            "problem_solving": _normalize_problem_solving(row.get("problem_solving")),
        }

    if mode == "concept":
        _reject_unknown_keys(
            row,
            field="analysis_packet",
            allowed={"mode", "knowledge_tree"},
        )
        return {
            "mode": "concept",
            "knowledge_tree": _normalize_knowledge_tree(row.get("knowledge_tree")),
        }

    raise AnalysisPacketError("mode 只能是 problem 或 concept")


def save_analysis_packet(path: Path, payload: Mapping[str, Any]) -> None:
    normalized = normalize_analysis_packet(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
