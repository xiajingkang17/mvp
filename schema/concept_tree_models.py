from __future__ import annotations

from collections import defaultdict, deque
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ConceptLevel = Literal["beginner", "intermediate", "advanced"]


class ConceptAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    core_concept: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    level: ConceptLevel
    goal: str = Field(min_length=1)


class ConceptNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    depth: int = Field(ge=0, le=8)
    is_foundation: bool
    rationale: str | None = None


class ConceptEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_id: str = Field(min_length=1)
    to_id: str = Field(min_length=1)
    relation: Literal["requires"] = "requires"


class ConceptTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: ConceptAnalysis
    root_id: str = Field(min_length=1)
    nodes: list[ConceptNode] = Field(default_factory=list, min_length=1)
    edges: list[ConceptEdge] = Field(default_factory=list)
    ordered_concepts: list[str] = Field(default_factory=list, min_length=1)
    explanation: str | None = None

    @model_validator(mode="after")
    def _validate_tree(self) -> "ConceptTree":
        id_to_node: dict[str, ConceptNode] = {}
        concept_to_id: dict[str, str] = {}
        for node in self.nodes:
            if node.id in id_to_node:
                raise ValueError(f"Duplicate node id: {node.id}")
            id_to_node[node.id] = node

            concept_key = node.concept.strip().lower()
            if concept_key in concept_to_id:
                raise ValueError(f"Duplicate concept name: {node.concept}")
            concept_to_id[concept_key] = node.id

        if self.root_id not in id_to_node:
            raise ValueError(f"root_id references unknown node id: {self.root_id}")

        roots = [node.id for node in self.nodes if node.depth == 0]
        if len(roots) != 1:
            raise ValueError("Knowledge tree must have exactly one depth-0 root node")
        if roots[0] != self.root_id:
            raise ValueError("root_id must match the unique depth-0 root node")

        root_node = id_to_node[self.root_id]
        if root_node.concept.strip().lower() != self.analysis.core_concept.strip().lower():
            raise ValueError("root node concept must match analysis.core_concept")

        outgoing: dict[str, list[str]] = defaultdict(list)
        indegree: dict[str, int] = {node_id: 0 for node_id in id_to_node}
        edge_seen: set[tuple[str, str]] = set()

        for edge in self.edges:
            if edge.from_id not in id_to_node:
                raise ValueError(f"Edge from_id references unknown node id: {edge.from_id}")
            if edge.to_id not in id_to_node:
                raise ValueError(f"Edge to_id references unknown node id: {edge.to_id}")
            if edge.from_id == edge.to_id:
                raise ValueError(f"Self-loop edge is not allowed: {edge.from_id}")

            pair = (edge.from_id, edge.to_id)
            if pair in edge_seen:
                raise ValueError(f"Duplicate edge: {edge.from_id} -> {edge.to_id}")
            edge_seen.add(pair)

            outgoing[edge.from_id].append(edge.to_id)
            indegree[edge.to_id] += 1

        for node in self.nodes:
            if node.is_foundation and outgoing.get(node.id):
                raise ValueError(f"Foundation node cannot have outgoing prerequisite edges: {node.id}")

        queue = deque([node_id for node_id, deg in indegree.items() if deg == 0])
        visited = 0
        while queue:
            node_id = queue.popleft()
            visited += 1
            for nxt in outgoing.get(node_id, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if visited != len(self.nodes):
            raise ValueError("Knowledge tree graph contains a cycle")

        ordered_keys = [name.strip().lower() for name in self.ordered_concepts if name.strip()]
        if len(ordered_keys) != len(self.ordered_concepts):
            raise ValueError("ordered_concepts contains empty entries")
        if len(set(ordered_keys)) != len(ordered_keys):
            raise ValueError("ordered_concepts must not contain duplicates")

        node_keys = set(concept_to_id.keys())
        if set(ordered_keys) != node_keys:
            missing = sorted(node_keys - set(ordered_keys))
            extra = sorted(set(ordered_keys) - node_keys)
            raise ValueError(
                f"ordered_concepts must be a full concept permutation; missing={missing}, extra={extra}"
            )

        ordered_index = {key: idx for idx, key in enumerate(ordered_keys)}
        for edge in self.edges:
            src_key = id_to_node[edge.from_id].concept.strip().lower()
            dst_key = id_to_node[edge.to_id].concept.strip().lower()
            if ordered_index[dst_key] >= ordered_index[src_key]:
                raise ValueError(
                    "ordered_concepts must list prerequisites before dependent concepts"
                )

        if not any(node.is_foundation for node in self.nodes):
            raise ValueError("Knowledge tree must contain at least one foundation concept")

        return self
