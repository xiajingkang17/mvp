from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _assert_unique_ids(kind: str, items: list[Any]) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.id
        if item_id in seen:
            raise ValueError(f"Duplicate {kind} id: {item_id}")
        seen.add(item_id)


def _iter_ref_values(args: dict[str, Any], key: str) -> list[str]:
    value = args.get(key)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _validate_reference_dict(
    *,
    prefix: str,
    args: dict[str, Any],
    part_ids: set[str],
    track_ids: set[str],
) -> None:
    part_ref_keys = (
        "part_id",
        "part_a",
        "part_b",
        "from_part_id",
        "to_part_id",
        "source_part_id",
        "target_part_id",
    )
    track_ref_keys = ("track_id", "source_track_id", "target_track_id")

    for key in part_ref_keys:
        for part_id in _iter_ref_values(args, key):
            if part_id not in part_ids:
                raise ValueError(f"{prefix}.{key} references unknown part id: {part_id}")

    for key in track_ref_keys:
        for track_id in _iter_ref_values(args, key):
            if track_id not in track_ids:
                raise ValueError(f"{prefix}.{key} references unknown track id: {track_id}")


class GraphSpace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_range: tuple[float, float] = (-10.0, 10.0)
    y_range: tuple[float, float] = (-6.0, 6.0)
    unit: str = "scene_unit"
    angle_unit: Literal["deg"] = "deg"
    origin: Literal["center"] = "center"

    @model_validator(mode="after")
    def _validate_ranges(self) -> "GraphSpace":
        if self.x_range[0] >= self.x_range[1]:
            raise ValueError("space.x_range must satisfy min < max")
        if self.y_range[0] >= self.y_range[1]:
            raise ValueError("space.y_range must satisfy min < max")
        return self


class SeedPose(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    scale: float = Field(default=1.0, gt=0)
    z: float = 0.0


class GraphPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    seed_pose: SeedPose = Field(default_factory=SeedPose)


class GraphTrack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: Literal["line", "segment", "arc"]
    data: dict[str, Any] = Field(default_factory=dict)


class GraphConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: Literal["attach", "on_segment", "midpoint", "align_axis", "distance"]
    args: dict[str, Any] = Field(default_factory=dict)
    hard: bool = True


class GraphMotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class CompositeGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    space: GraphSpace = Field(default_factory=GraphSpace)
    parts: list[GraphPart] = Field(default_factory=list)
    tracks: list[GraphTrack] = Field(default_factory=list)
    constraints: list[GraphConstraint] = Field(default_factory=list)
    motions: list[GraphMotion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_ids_and_refs(self) -> "CompositeGraph":
        _assert_unique_ids("parts", self.parts)
        _assert_unique_ids("tracks", self.tracks)
        _assert_unique_ids("constraints", self.constraints)
        _assert_unique_ids("motions", self.motions)

        part_ids = {part.id for part in self.parts}
        track_ids = {track.id for track in self.tracks}

        for index, constraint in enumerate(self.constraints):
            _validate_reference_dict(
                prefix=f"constraints[{index}].args",
                args=constraint.args,
                part_ids=part_ids,
                track_ids=track_ids,
            )

        for index, motion in enumerate(self.motions):
            _validate_reference_dict(
                prefix=f"motions[{index}].args",
                args=motion.args,
                part_ids=part_ids,
                track_ids=track_ids,
            )

        return self
