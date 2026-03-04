from __future__ import annotations

import math
import numpy as np
from manim import *


class Wall(VGroup):
    """墙面/地面组件，包含主线与阴影短线。"""

    def __init__(
        self,
        length: float = 8.0,
        angle: float = 0,
        rise_to: str = "right",
        hatch_spacing: float = 0.4,
        hatch_length: float = 0.25,
        contact_offset_y: float = 0.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_value = float(angle)
        rise_to_value = str(rise_to).strip().lower()
        if rise_to_value not in {"left", "right"}:
            raise ValueError("rise_to must be 'left' or 'right'")
        if angle_value < 0:
            angle_value = abs(angle_value)
            if rise_to_value == "right":
                rise_to_value = "left"
        if angle_value > 90:
            raise ValueError("Wall angle must be in [0, 90] degrees")

        main_line = Line(
            start=[-length/2, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        hatch_lines = VGroup()
        num_hatches = int(length / hatch_spacing)

        hatch_angle = -45 * DEGREES
        hatch_direction = np.array([
            math.cos(hatch_angle),
            math.sin(hatch_angle),
            0
        ])

        for i in range(num_hatches):
            x = -length/2 + i * hatch_spacing

            start_point = np.array([x, 0, 0])

            end_point = start_point + hatch_direction * hatch_length

            hatch = Line(
                start=start_point,
                end=end_point,
                color=color,
                stroke_width=stroke_width * 0.6
            )
            hatch_lines.add(hatch)

        self.add(main_line, hatch_lines)
        signed_angle = angle_value if rise_to_value == "right" else -angle_value
        if signed_angle != 0.0:
            self.rotate(signed_angle * DEGREES, about_point=ORIGIN)

        if float(contact_offset_y) != 0.0:
            self.shift(UP * float(contact_offset_y))
