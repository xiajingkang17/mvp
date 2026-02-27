from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schema.scene_plan_models import PedagogyPlan


class SemanticObjectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=2, ge=1, le=9)
    anchor: str | None = None
    z_index: int | None = None

    @model_validator(mode="after")
    def _validate_semantic_object(self) -> "SemanticObjectSpec":
        if self.type == "CompositeObject" and isinstance(self.params, dict) and "graph" in self.params:
            raise ValueError("CompositeObject params must not include graph in scene_semantic")
        return self


class StoryboardFormula(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latex: str = Field(min_length=1)
    color: str | None = None
    position_hint: str | None = None
    duration_s: float | None = Field(default=None, gt=0)


class StoryboardStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    targets: list[str] = Field(default_factory=list)
    color_hint: str | None = None
    position_hint: str | None = None
    duration_s: float = Field(gt=0)

    @model_validator(mode="after")
    def _validate_targets(self) -> "StoryboardStep":
        cleaned = [str(x).strip() for x in self.targets if str(x).strip()]
        if not cleaned:
            raise ValueError("narrative_storyboard.animation_steps[].targets must be non-empty")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("narrative_storyboard.animation_steps[].targets contains duplicates")
        self.targets = cleaned
        return self


class NarrativeStoryboard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bridge_from_prev: str = ""
    intro: str = Field(min_length=1)
    key_formulae: list[StoryboardFormula] = Field(default_factory=list)
    animation_steps: list[StoryboardStep] = Field(default_factory=list, min_length=1)
    bridge_to_next: str = ""

    @model_validator(mode="after")
    def _validate_step_ids(self) -> "NarrativeStoryboard":
        seen: set[str] = set()
        for step in self.animation_steps:
            sid = step.id.strip()
            if sid in seen:
                raise ValueError(f"duplicate animation step id: {sid}")
            seen.add(sid)
        return self


class SemanticSceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    intent: str | None = None
    goal: str | None = None
    modules: list[str] = Field(default_factory=list)
    roles: dict[str, str] = Field(default_factory=dict)
    new_symbols: list[str] = Field(default_factory=list)
    is_check_scene: bool = False
    notes: str | None = None
    objects: list[SemanticObjectSpec] = Field(default_factory=list)
    narrative_storyboard: NarrativeStoryboard

    @model_validator(mode="after")
    def _validate_scene_refs(self) -> "SemanticSceneSpec":
        object_ids = {obj.id for obj in self.objects}
        for object_id in self.roles:
            if object_id not in object_ids:
                raise ValueError(f"roles references unknown object id: {object_id}")
        return self


class SceneSemanticPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    pedagogy_plan: PedagogyPlan | None = None
    scenes: list[SemanticSceneSpec] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def _validate_plan(self) -> "SceneSemanticPlan":
        seen_scene_ids: set[str] = set()
        for scene in self.scenes:
            if scene.id in seen_scene_ids:
                raise ValueError(f"duplicate scene id: {scene.id}")
            seen_scene_ids.add(scene.id)

        if len(self.scenes) > 1:
            for index, scene in enumerate(self.scenes):
                if index >= len(self.scenes) - 1:
                    continue
                if not scene.narrative_storyboard.bridge_to_next.strip():
                    raise ValueError(
                        f"scenes[{index}].narrative_storyboard.bridge_to_next required for non-final scene"
                    )
        return self
