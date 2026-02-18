from __future__ import annotations

from typing import Any

from render.composite.types import PartGeometry, Pose


def arg(args: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in args:
            return args[key]
    return default


def anchor_name(args: dict[str, Any], *keys: str, default: str = "center") -> str:
    value = arg(args, *keys, default=default)
    return str(value or default)


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    from math import hypot

    return hypot(ax - bx, ay - by)


def part_or_raise(
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    part_id: str,
    field: str,
) -> tuple[Pose, PartGeometry]:
    if part_id not in poses or part_id not in geoms:
        raise ValueError(f"{field} references unknown part id: {part_id}")
    return poses[part_id], geoms[part_id]


def resolve_point_ref(
    *,
    args: dict[str, Any],
    index: int,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> tuple[float, float]:
    from render.composite.types import anchor_world

    part_key = f"part_{index}"
    anchor_key = f"anchor_{index}"
    point_key = f"point_{index}"

    explicit = args.get(point_key)
    if isinstance(explicit, (list, tuple)) and len(explicit) >= 2:
        return to_float(explicit[0]), to_float(explicit[1])

    part_id = arg(args, part_key, default=None)
    if isinstance(part_id, str):
        pose, geom = part_or_raise(poses, geoms, part_id, part_key)
        local = geom.anchor_local(anchor_name(args, anchor_key, default="center"))
        return anchor_world(pose, local)

    x = args.get(f"x{index}")
    y = args.get(f"y{index}")
    if x is not None and y is not None:
        return to_float(x), to_float(y)

    raise ValueError(f"Cannot resolve point_{index} from args")

