from __future__ import annotations

from manim import *


class Spring(VGroup):
    """弹簧组件。"""

    def __init__(
        self,
        length: float = 4.0,
        height: float = 0.6,
        num_coils: int = 8,
        end_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        coil_width = (length - 2 * end_length) / num_coils

        left_end = Line(
            start=[-length/2, 0, 0],
            end=[-length/2 + end_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.left_end_line = left_end

        zigzag_points = [[-length/2 + end_length, 0, 0]]

        for i in range(num_coils):
            x_start = -length/2 + end_length + i * coil_width
            zigzag_points.append([x_start + coil_width/2, height/2, 0])
            zigzag_points.append([x_start + coil_width, -height/2, 0])

        zigzag_points.append([length/2 - end_length, 0, 0])

        zigzag = VMobject()
        zigzag.set_points_as_corners(zigzag_points)
        zigzag.set_color(color)
        zigzag.set_stroke(width=stroke_width)
        self.zigzag = zigzag

        right_end = Line(
            start=[length/2 - end_length, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.right_end_line = right_end

        self.add(left_end, zigzag, right_end)
