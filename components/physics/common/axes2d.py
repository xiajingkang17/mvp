from __future__ import annotations

from typing import Dict, List

import numpy as np
from manim import Axes, Tex, VGroup, VectorizedPoint, WHITE


class Axes2D(VGroup):
    """Reusable 2D coordinate axes for physics/electromagnetism scenes."""

    def __init__(
        self,
        x_min: float = -5.0,
        x_max: float = 5.0,
        y_min: float = -3.0,
        y_max: float = 3.0,
        x_step: float = 1.0,
        y_step: float = 1.0,
        x_length: float = 8.0,
        y_length: float = 5.0,
        show_ticks: bool = False,
        show_numbers: bool = False,
        show_labels: bool = True,
        label_x: str = "x",
        label_y: str = "y",
        label_color: str = WHITE,
        color: str = WHITE,
        stroke_width: float = 3.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        x_min_v = float(x_min)
        x_max_v = float(x_max)
        y_min_v = float(y_min)
        y_max_v = float(y_max)
        if x_max_v <= x_min_v:
            raise ValueError("Axes2D requires x_max > x_min")
        if y_max_v <= y_min_v:
            raise ValueError("Axes2D requires y_max > y_min")

        axis_config = {
            "color": color,
            "stroke_width": float(stroke_width),
            "include_ticks": bool(show_ticks),
            "include_tip": True,
            "include_numbers": bool(show_numbers),
        }
        axes = Axes(
            x_range=[x_min_v, x_max_v, float(x_step)],
            y_range=[y_min_v, y_max_v, float(y_step)],
            x_length=float(x_length),
            y_length=float(y_length),
            axis_config=axis_config,
        )
        self.axes = axes
        self.add(axes)

        if bool(show_labels):
            x_label = Tex(str(label_x), color=label_color).scale(0.7)
            y_label = Tex(str(label_y), color=label_color).scale(0.7)
            labels = axes.get_axis_labels(x_label, y_label)
            self.add(labels)

        self._init_anchors(axes=axes, x_min=x_min_v, x_max=x_max_v, y_min=y_min_v, y_max=y_max_v)

    def _init_anchors(self, *, axes: Axes, x_min: float, x_max: float, y_min: float, y_max: float) -> None:
        points = {
            "center": np.array(axes.get_center()),
            "origin": np.array(axes.c2p(0.0, 0.0)),
            "x_start": np.array(axes.c2p(x_min, 0.0)),
            "x_end": np.array(axes.c2p(x_max, 0.0)),
            "y_start": np.array(axes.c2p(0.0, y_min)),
            "y_end": np.array(axes.c2p(0.0, y_max)),
            "top_left": np.array(axes.c2p(x_min, y_max)),
            "top_right": np.array(axes.c2p(x_max, y_max)),
            "bottom_left": np.array(axes.c2p(x_min, y_min)),
            "bottom_right": np.array(axes.c2p(x_max, y_min)),
        }
        for name, point in points.items():
            anchor = VectorizedPoint(point)
            self._anchor_points[name] = anchor
            self.add(anchor)

    def list_anchors(self) -> List[str]:
        return list(self._anchor_points.keys())

    def get_anchor(self, name: str) -> np.ndarray:
        key = str(name).strip()
        if key not in self._anchor_points:
            available = ", ".join(self.list_anchors())
            raise ValueError(f"Unknown anchor '{name}'. Available: {available}")
        return np.array(self._anchor_points[key].get_center())
