from __future__ import annotations

from typing import Any

from schema.composite_graph_models import CompositeGraph

from .types import PartGeometry, Pose, anchor_world, rotate_vec


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def _space(data: dict[str, Any]) -> str:
    return str(data.get("space", "local")).strip().lower()


def _transform_local_point(pose: Pose, local_point: tuple[float, float]) -> tuple[float, float]:
    rx, ry = rotate_vec(local_point[0] * pose.scale, local_point[1] * pose.scale, pose.theta)
    return pose.x + rx, pose.y + ry


def _bake_line_or_segment(
    *,
    data: dict[str, Any],
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
) -> dict[str, Any]:
    if _space(data) == "world":
        return dict(data)

    has_legacy_local_points = any(
        key in data for key in ("p1_local", "p2_local", "x1_local", "y1_local", "x2_local", "y2_local")
    )
    if has_legacy_local_points:
        raise ValueError("local line/segment track forbids p1_local/p2_local/x*_local; use anchor_a/anchor_b")

    part_id = str(data.get("part_id", "")).strip()
    if not part_id or part_id not in poses or part_id not in geometries:
        raise ValueError("local line/segment track requires valid data.part_id")

    pose = poses[part_id]
    geom = geometries[part_id]

    a_name = str(data.get("anchor_a") or data.get("a1") or "").strip()
    b_name = str(data.get("anchor_b") or data.get("a2") or "").strip()
    if not (a_name and b_name):
        raise ValueError("local line/segment track requires anchor_a and anchor_b")

    local_a = geom.anchor_local(a_name)
    local_b = geom.anchor_local(b_name)
    world_a = anchor_world(pose, local_a)
    world_b = anchor_world(pose, local_b)
    return {
        "space": "world",
        "x1": float(world_a[0]),
        "y1": float(world_a[1]),
        "x2": float(world_b[0]),
        "y2": float(world_b[1]),
    }


def _bake_arc(
    *,
    data: dict[str, Any],
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
) -> dict[str, Any]:
    if _space(data) == "world":
        return dict(data)

    has_legacy_arc_fields = any(
        key in data
        for key in (
            "center",
            "center_local",
            "cx",
            "cy",
            "radius",
            "r",
            "start_deg",
            "end_deg",
            "start_angle",
            "end_angle",
        )
    )
    if has_legacy_arc_fields:
        raise ValueError(
            "local arc track forbids center/radius/world-angle fields; use center_anchor|cx_local+cy_local + radius_local + local angles"
        )

    part_id = str(data.get("part_id", "")).strip()
    if not part_id or part_id not in poses or part_id not in geometries:
        raise ValueError("local arc track requires valid data.part_id")

    pose = poses[part_id]
    geom = geometries[part_id]

    center_anchor = str(data.get("center_anchor", "")).strip()
    if center_anchor:
        local_center = geom.anchor_local(center_anchor)
    else:
        if not (isinstance(data.get("cx_local"), (int, float)) and isinstance(data.get("cy_local"), (int, float))):
            raise ValueError("local arc track requires center_anchor or cx_local+cy_local")
        local_center = (_to_float(data.get("cx_local")), _to_float(data.get("cy_local")))

    world_center = _transform_local_point(pose, local_center)
    if "radius_local" in data:
        radius_local = _to_float(data.get("radius_local"))
    elif "r_local" in data:
        radius_local = _to_float(data.get("r_local"))
    else:
        raise ValueError("local arc track requires radius_local or r_local")

    if "start_deg_local" in data and "end_deg_local" in data:
        start_local = _to_float(data.get("start_deg_local"))
        end_local = _to_float(data.get("end_deg_local"))
    elif "start_angle_local" in data and "end_angle_local" in data:
        start_local = _to_float(data.get("start_angle_local"))
        end_local = _to_float(data.get("end_angle_local"))
    else:
        raise ValueError("local arc track requires start/end local angles")

    return {
        "space": "world",
        "cx": float(world_center[0]),
        "cy": float(world_center[1]),
        "r": abs(float(pose.scale)) * float(radius_local),
        "start_deg": float(pose.theta) + float(start_local),
        "end_deg": float(pose.theta) + float(end_local),
    }


def bake_local_tracks_to_world(
    graph: CompositeGraph,
    *,
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
) -> CompositeGraph:
    baked_tracks = []
    for track in graph.tracks:
        data = dict(track.data or {})
        ttype = str(track.type).strip().lower()
        if ttype in {"line", "segment"}:
            baked_data = _bake_line_or_segment(data=data, poses=poses, geometries=geometries)
        elif ttype == "arc":
            baked_data = _bake_arc(data=data, poses=poses, geometries=geometries)
        else:
            baked_data = dict(data)
        baked_tracks.append(track.model_copy(update={"data": baked_data}))
    return graph.model_copy(update={"tracks": baked_tracks})
