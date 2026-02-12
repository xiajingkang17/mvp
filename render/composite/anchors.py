from __future__ import annotations

from render.composite.types import PartGeometry


def default_anchor_map(*, width: float, height: float) -> dict[str, tuple[float, float]]:
    w2 = float(width) / 2.0
    h2 = float(height) / 2.0
    return {
        "center": (0.0, 0.0),
        "bottom_center": (0.0, -h2),
        "top_center": (0.0, h2),
        "left_center": (-w2, 0.0),
        "right_center": (w2, 0.0),
        "bottom_left": (-w2, -h2),
        "bottom_right": (w2, -h2),
        "top_left": (-w2, h2),
        "top_right": (w2, h2),
    }


def geometry_from_mobject(part_id: str, mobj) -> PartGeometry:
    # We approximate anchors from bbox. This is generic and works for all component types.
    width = float(getattr(mobj, "width", 0.0))
    height = float(getattr(mobj, "height", 0.0))
    anchors = default_anchor_map(width=width, height=height)
    return PartGeometry(part_id=part_id, anchors=anchors)
