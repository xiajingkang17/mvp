from __future__ import annotations

"""
analysis_packet 契约常量。
用于统一 schema / validator / 测试。
"""

MIN_KNOWN_CONDITIONS = 1
MIN_PROBLEM_SOLVING_STEPS = 1
MIN_STEP_EQUATIONS = 1
MIN_ANSWER_CHECK_ITEMS = 1

MIN_KNOWLEDGE_TREE_NODES = 2
MIN_KNOWLEDGE_TREE_EDGES = 1

NODE_TYPES = {"target", "prerequisite", "bridge"}
EDGE_RELATIONS = {"prerequisite"}
