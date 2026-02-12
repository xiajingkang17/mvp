from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ContentItem = Literal[
    "hook_question",
    "goal",
    "knowns",
    "diagram",
    "assumption",
    "principle",
    "core_equation",
    "derive_step",
    "substitute_compute",
    "intermediate_result",
    "conclusion",
    "check_sanity",
    "transition",
]

DerivationStepType = Literal["equation", "compute", "reasoning", "diagram_note"]


class SymbolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    meaning: str = Field(min_length=1)
    unit: str | None = None


class MethodChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class DerivationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: DerivationStepType
    content: str = Field(min_length=1)


class ResultSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str = Field(min_length=1)
    unit: str | None = None
    text: str | None = None


class ScenePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_items: list[ContentItem] = Field(default_factory=list, min_length=1, max_length=5)
    primary_item: ContentItem
    emphasis: str | None = None

    @model_validator(mode="after")
    def _validate_primary_item(self) -> "ScenePacket":
        if self.primary_item not in self.content_items:
            raise ValueError("primary_item must appear in content_items")
        return self


class SubQuestionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    question: str | None = None
    goal: str = Field(min_length=1)
    device_scene_needed: bool = True
    variable_annotations: list[str] = Field(default_factory=list)
    given_conditions: list[str] = Field(default_factory=list)
    method_choice: MethodChoice
    derivation_steps: list[DerivationStep] = Field(default_factory=list, min_length=1)
    result: ResultSpec
    sanity_checks: list[str] = Field(default_factory=list)
    transition: str | None = None
    scene_packets: list[ScenePacket] = Field(default_factory=list, min_length=1)


class TeachingPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explanation_full: str = Field(min_length=1)
    global_symbols: list[SymbolSpec] = Field(default_factory=list)
    sub_questions: list[SubQuestionPlan] = Field(default_factory=list, min_length=1)

