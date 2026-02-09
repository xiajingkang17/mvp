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


class ScenePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    meta: dict[str, Any] = Field(default_factory=dict)
    objects: dict[str, ObjectSpec] = Field(default_factory=dict)
    scenes: list[SceneSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_unique_scene_ids(self) -> "ScenePlan":
        seen: set[str] = set()
        for scene in self.scenes:
            if scene.id in seen:
                raise ValueError(f"Duplicate scene id: {scene.id}")
            seen.add(scene.id)
        return self

