from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schema.composite_graph_models import CompositeGraph


class DrawCompositeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(min_length=1)
    graph: CompositeGraph


class DrawSceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    composites: list[DrawCompositeSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_composite_ids(self) -> "DrawSceneSpec":
        seen: set[str] = set()
        for item in self.composites:
            oid = item.object_id.strip()
            if oid in seen:
                raise ValueError(f"duplicate composites.object_id in scene '{self.id}': {oid}")
            seen.add(oid)
        return self


class SceneDrawPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    scenes: list[DrawSceneSpec] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def _validate_scene_ids(self) -> "SceneDrawPlan":
        seen: set[str] = set()
        for scene in self.scenes:
            sid = scene.id.strip()
            if sid in seen:
                raise ValueError(f"duplicate scene id: {sid}")
            seen.add(sid)
        return self
