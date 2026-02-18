from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class SpringScale(VGroup):
    """弹簧测力计组件。"""

    def __init__(
        self,
        width: float = 1.0,
        height: float = 3.5,
        reading: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        body = Rectangle(
            width=width,
            height=height,
            color=color,
            stroke_width=stroke_width
        )
        body.set_fill(BLACK, opacity=1)
        body.move_to(ORIGIN)

        padding = height * 0.15
        top_y = body.get_top()[1] - padding
        bottom_y = body.get_bottom()[1] + padding

        center_line = Line(
            start=[0, top_y, 0],
            end=[0, bottom_y, 0],
            color=color,
            stroke_width=stroke_width * 0.5
        )

        scale_marks = VGroup()
        num_major_ticks = 5
        num_minor_ticks = 20

        for i in range(num_minor_ticks + 1):
            alpha = i / num_minor_ticks
            y = top_y * (1 - alpha) + bottom_y * alpha

            is_major = (i % (num_minor_ticks // num_major_ticks) == 0)
            mark_length = width * 0.35 if is_major else width * 0.2
            mark_width = stroke_width * 0.8 if is_major else stroke_width * 0.5

            tick_start_x = -width/2 + 0.1
            tick = Line(
                start=[tick_start_x, y, 0],
                end=[tick_start_x + mark_length, y, 0],
                color=color,
                stroke_width=mark_width
            )
            scale_marks.add(tick)

            if is_major:
                tick_num = i // (num_minor_ticks // num_major_ticks)
                label = Text(
                    str(tick_num),
                    font_size=16,
                    color=color
                )
                label.move_to([tick_start_x + mark_length + 0.15, y, 0])
                scale_marks.add(label)

        alpha = reading
        pointer_y = top_y * (1 - alpha) + bottom_y * alpha

        pointer = Line(
            start=[-width * 0.25, pointer_y, 0],
            end=[width * 0.25, pointer_y, 0],
            color=YELLOW,
            stroke_width=stroke_width * 0.8
        )

        arrowhead = Polygon(
            [width * 0.25, pointer_y, 0],
            [width * 0.15, pointer_y - 0.08, 0],
            [width * 0.15, pointer_y + 0.08, 0],
            color=YELLOW,
            stroke_width=stroke_width * 0.6
        )
        arrowhead.set_fill(YELLOW, opacity=1)

        ring_radius = width * 0.25
        top_ring = Annulus(
            inner_radius=ring_radius * 0.6,
            outer_radius=ring_radius,
            color=color,
            stroke_width=stroke_width
        )
        top_ring.next_to(body, UP, buff=0)
        top_ring.set_x(0)

        hook_radius = width * 0.15
        hook = Arc(
            radius=hook_radius,
            start_angle=PI,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )
        hook.rotate(-PI/2)
        hook.next_to(body, DOWN, buff=0)
        hook.set_x(0)

        self.add(body, center_line, scale_marks, pointer, arrowhead, top_ring, hook)
