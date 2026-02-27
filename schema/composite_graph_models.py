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

    @model_validator(mode="before")
    @classmethod
    def _normalize_track_data_alias(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw = dict(data)

        if "data" not in raw and isinstance(raw.get("params"), dict):
            raw["data"] = dict(raw.pop("params"))
        elif "data" in raw and "params" in raw:
            raw.pop("params", None)

        payload = raw.get("data")
        if not isinstance(payload, dict):
            return raw
        payload = dict(payload)
        track_type = str(raw.get("type", "")).strip().lower()

        def _is_number(value: Any) -> bool:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if track_type == "arc":
            if "space" not in payload:
                raise ValueError("arc track data requires explicit space")
            allowed_arc_keys = {
                "space",
                "part_id",
                "center",
                "cx",
                "cy",
                "radius",
                "start",
                "end",
            }
            unknown = sorted(key for key in payload.keys() if key not in allowed_arc_keys)
            if unknown:
                raise ValueError(
                    "arc track data has unknown keys; use canonical fields only: "
                    + ", ".join(unknown)
                )
            required = [key for key in ("space", "radius", "start", "end") if key not in payload]
            if required:
                raise ValueError("arc track data missing required keys: " + ", ".join(required))
            if "center" in payload and not isinstance(payload.get("center"), str):
                raise ValueError("arc track data.center must be an anchor name string")

            arc_space = str(payload.get("space", "")).strip().lower()
            if arc_space not in {"local", "world"}:
                raise ValueError("arc track data.space must be local/world")

            if arc_space == "local":
                part_id = payload.get("part_id")
                if not isinstance(part_id, str) or not part_id.strip():
                    raise ValueError("local arc track requires part_id")
                has_center_anchor = isinstance(payload.get("center"), str) and bool(str(payload.get("center")).strip())
                has_center_xy = _is_number(payload.get("cx")) and _is_number(payload.get("cy"))
                if not (has_center_anchor or has_center_xy):
                    raise ValueError("local arc track requires center or cx/cy")
            else:
                if "part_id" in payload:
                    raise ValueError("world arc track forbids part_id")
                if "center" in payload:
                    raise ValueError("world arc track forbids center anchor")
                if not (_is_number(payload.get("cx")) and _is_number(payload.get("cy"))):
                    raise ValueError("world arc track requires cx/cy")

            raw["data"] = payload
            return raw

        if track_type == "segment":
            allowed_segment_keys = {
                "space",
                "part_id",
                "anchor_a",
                "anchor_b",
                "x1",
                "y1",
                "x2",
                "y2",
            }
            unknown = sorted(key for key in payload.keys() if key not in allowed_segment_keys)
            if unknown:
                raise ValueError(
                    "segment track data has unknown keys; use canonical fields only: "
                    + ", ".join(unknown)
                )

            if "space" not in payload:
                has_world_coords = all(_is_number(payload.get(key)) for key in ("x1", "y1", "x2", "y2"))
                payload["space"] = "world" if has_world_coords else "local"

            seg_space = str(payload.get("space", "")).strip().lower()
            if seg_space not in {"local", "world"}:
                raise ValueError("segment track data.space must be local/world")

            if seg_space == "local":
                part_id = payload.get("part_id")
                if not isinstance(part_id, str) or not part_id.strip():
                    raise ValueError("local segment track requires part_id")
                anchor_a = payload.get("anchor_a")
                anchor_b = payload.get("anchor_b")
                if not isinstance(anchor_a, str) or not anchor_a.strip():
                    raise ValueError("local segment track requires anchor_a")
                if not isinstance(anchor_b, str) or not anchor_b.strip():
                    raise ValueError("local segment track requires anchor_b")
                if any(key in payload for key in ("x1", "y1", "x2", "y2")):
                    raise ValueError("local segment track forbids x1/y1/x2/y2")
            else:
                if any(key in payload for key in ("part_id", "anchor_a", "anchor_b")):
                    raise ValueError("world segment track forbids part_id/anchor_a/anchor_b")
                if not all(_is_number(payload.get(key)) for key in ("x1", "y1", "x2", "y2")):
                    raise ValueError("world segment track requires x1/y1/x2/y2")

        raw["data"] = payload
        return raw


class GraphConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: Literal["attach", "midpoint", "distance", "on_track_pose"]
    args: dict[str, Any] = Field(default_factory=dict)
    hard: bool = True

    @model_validator(mode="before")
    @classmethod
    def _normalize_params_alias(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "args" not in data and isinstance(data.get("params"), dict):
            data = dict(data)
            data["args"] = dict(data.pop("params"))
        elif "args" in data and "params" in data:
            data = dict(data)
            data.pop("params", None)
        return data


class GraphMotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_params_alias(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "args" not in data and isinstance(data.get("params"), dict):
            data = dict(data)
            data["args"] = dict(data.pop("params"))
        elif "args" in data and "params" in data:
            data = dict(data)
            data.pop("params", None)
        return data


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
