from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObjectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=2, ge=1, le=9)
    anchor: str | None = None
    z_index: int | None = None


class LayoutSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    slots: dict[str, str] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)


class CognitiveBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_visible_objects: int = Field(default=4, ge=1, le=9)
    max_new_formula: int = Field(default=4, ge=1, le=9)
    max_new_symbols: int = Field(default=3, ge=0, le=20)
    max_text_chars: int = Field(default=60, ge=8, le=200)


class PedagogyPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    difficulty: Literal["simple", "medium", "hard"] = "medium"
    need_single_goal: bool = False
    need_check_scene: bool = False
    check_types: list[Literal["unit", "boundary", "feasibility", "reasonableness"]] = Field(default_factory=list)
    cognitive_budget: CognitiveBudget = Field(default_factory=CognitiveBudget)
    module_order: list[str] = Field(default_factory=list)


class PlayAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["play"]
    anim: str = Field(min_length=1)
    targets: list[str] = Field(default_factory=list)
    src: str | None = None
    dst: str | None = None
    duration: float | None = Field(default=None, gt=0)
    kwargs: dict[str, Any] = Field(default_factory=dict)


class WaitAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["wait"]
    duration: float = Field(ge=0)


ActionSpec = PlayAction | WaitAction


class SceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    intent: str | None = None
    layout: LayoutSpec
    actions: list[ActionSpec] = Field(default_factory=list)
    keep: list[str] = Field(default_factory=list)
    notes: str | None = None
    goal: str | None = None
    modules: list[str] = Field(default_factory=list)
    roles: dict[str, str] = Field(default_factory=dict)
    new_symbols: list[str] = Field(default_factory=list)
    is_check_scene: bool = False


class ScenePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    meta: dict[str, Any] = Field(default_factory=dict)
    objects: dict[str, ObjectSpec] = Field(default_factory=dict)
    scenes: list[SceneSpec] = Field(default_factory=list)
    pedagogy_plan: PedagogyPlan | None = None

    @model_validator(mode="after")
    def _validate_unique_scene_ids(self) -> "ScenePlan":
        seen: set[str] = set()
        for scene in self.scenes:
            if scene.id in seen:
                raise ValueError(f"Duplicate scene id: {scene.id}")
            seen.add(scene.id)
        return self

