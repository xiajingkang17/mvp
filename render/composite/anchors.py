from __future__ import annotations

import numpy as np

from render.composite.types import PartGeometry


def default_anchor_map(*, width: float, height: float) -> dict[str, tuple[float, float]]:
    _ = float(width), float(height)
    return {
        "center": (0.0, 0.0),
    }


def geometry_from_mobject(part_id: str, mobj) -> PartGeometry:
    anchors: dict[str, tuple[float, float]] = {}

    # Preserve only semantic anchors exposed by components (e.g. start/end).
    # Convert world coordinates to local coordinates relative to object center.
    list_anchors = getattr(mobj, "list_anchors", None)
    get_anchor = getattr(mobj, "get_anchor", None)
    if callable(list_anchors) and callable(get_anchor):
        center = np.array(mobj.get_center(), dtype=float).reshape(-1)
        for name in list_anchors():
            key = str(name).strip().lower()
            if not key:
                continue
            try:
                point = np.array(get_anchor(name), dtype=float).reshape(-1)
            except Exception:  # noqa: BLE001
                continue
            if point.size < 2 or center.size < 2:
                continue
            anchors[key] = (float(point[0] - center[0]), float(point[1] - center[1]))

    if "center" not in anchors:
        anchors["center"] = (0.0, 0.0)

    return PartGeometry(part_id=part_id, anchors=anchors)
