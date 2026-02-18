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

        def _has_any(*keys: str) -> bool:
            return any(key in payload for key in keys)

        if "p1" in payload and isinstance(payload.get("p1"), dict):
            p1 = payload.get("p1", {})
            if "x1" not in payload and isinstance(p1.get("x"), (int, float)):
                payload["x1"] = float(p1["x"])
            if "y1" not in payload and isinstance(p1.get("y"), (int, float)):
                payload["y1"] = float(p1["y"])
        if "p2" in payload and isinstance(payload.get("p2"), dict):
            p2 = payload.get("p2", {})
            if "x2" not in payload and isinstance(p2.get("x"), (int, float)):
                payload["x2"] = float(p2["x"])
            if "y2" not in payload and isinstance(p2.get("y"), (int, float)):
                payload["y2"] = float(p2["y"])

        if "center" in payload and isinstance(payload.get("center"), dict):
            center = payload.get("center", {})
            if "cx" not in payload and isinstance(center.get("x"), (int, float)):
                payload["cx"] = float(center["x"])
            if "cy" not in payload and isinstance(center.get("y"), (int, float)):
                payload["cy"] = float(center["y"])
        elif "center" in payload and isinstance(payload.get("center"), (list, tuple)):
            center_seq = list(payload.get("center") or [])
            if len(center_seq) >= 2:
                if "cx" not in payload and isinstance(center_seq[0], (int, float)):
                    payload["cx"] = float(center_seq[0])
                if "cy" not in payload and isinstance(center_seq[1], (int, float)):
                    payload["cy"] = float(center_seq[1])

        if "center_local" in payload and isinstance(payload.get("center_local"), dict):
            center_local = payload.get("center_local", {})
            if "cx_local" not in payload and isinstance(center_local.get("x"), (int, float)):
                payload["cx_local"] = float(center_local["x"])
            if "cy_local" not in payload and isinstance(center_local.get("y"), (int, float)):
                payload["cy_local"] = float(center_local["y"])
        elif "center_local" in payload and isinstance(payload.get("center_local"), (list, tuple)):
            center_local_seq = list(payload.get("center_local") or [])
            if len(center_local_seq) >= 2:
                if "cx_local" not in payload and isinstance(center_local_seq[0], (int, float)):
                    payload["cx_local"] = float(center_local_seq[0])
                if "cy_local" not in payload and isinstance(center_local_seq[1], (int, float)):
                    payload["cy_local"] = float(center_local_seq[1])

        if "p1_local" in payload and isinstance(payload.get("p1_local"), dict):
            p1_local = payload.get("p1_local", {})
            if "x1_local" not in payload and isinstance(p1_local.get("x"), (int, float)):
                payload["x1_local"] = float(p1_local["x"])
            if "y1_local" not in payload and isinstance(p1_local.get("y"), (int, float)):
                payload["y1_local"] = float(p1_local["y"])
        if "p2_local" in payload and isinstance(payload.get("p2_local"), dict):
            p2_local = payload.get("p2_local", {})
            if "x2_local" not in payload and isinstance(p2_local.get("x"), (int, float)):
                payload["x2_local"] = float(p2_local["x"])
            if "y2_local" not in payload and isinstance(p2_local.get("y"), (int, float)):
                payload["y2_local"] = float(p2_local["y"])

        if "a0" in payload and "start_deg" not in payload:
            payload["start_deg"] = payload["a0"]
        if "a1" in payload and "end_deg" not in payload:
            payload["end_deg"] = payload["a1"]
        if "start_angle" in payload and "start_deg" not in payload:
            payload["start_deg"] = payload["start_angle"]
        if "end_angle" in payload and "end_deg" not in payload:
            payload["end_deg"] = payload["end_angle"]
        if "start_angle_local" in payload and "start_deg_local" not in payload:
            payload["start_deg_local"] = payload["start_angle_local"]
        if "end_angle_local" in payload and "end_deg_local" not in payload:
            payload["end_deg_local"] = payload["end_angle_local"]

        if "r_local" in payload and "radius_local" not in payload:
            payload["radius_local"] = payload["r_local"]

        if "space" not in payload:
            has_local_hint = _has_any(
                "part_id",
                "anchor_a",
                "anchor_b",
                "a1",
                "a2",
                "p1_local",
                "p2_local",
                "x1_local",
                "y1_local",
                "x2_local",
                "y2_local",
                "center_local",
                "cx_local",
                "cy_local",
                "radius_local",
                "r_local",
                "start_deg_local",
                "end_deg_local",
                "start_angle_local",
                "end_angle_local",
            )
            has_world_hint = _has_any("x1", "y1", "x2", "y2", "cx", "cy", "start_deg", "end_deg", "x0", "y0", "dx", "dy")
            payload["space"] = "local" if has_local_hint or not has_world_hint else "world"

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
