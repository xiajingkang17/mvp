# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全箭头写法。

from manim import *
import numpy as np


def make_direction_arrow():
    arrow = Arrow(
        start=np.array([-1.0, 0.0, 0.0]),
        end=np.array([1.0, 0.0, 0.0]),
        buff=0.0,
        stroke_width=4,
        max_tip_length_to_length_ratio=0.18,
        color=YELLOW,
    )
    label = Text("v0", font_size=28, color=YELLOW).next_to(arrow, UP, buff=0.12)
    return VGroup(arrow, label)


def make_field_arrow_array():
    arrows = VGroup(*[
        Arrow(
            start=np.array([x, -0.25, 0.0]),
            end=np.array([x, 0.25, 0.0]),
            buff=0.0,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.2,
            color=BLUE,
        )
        for x in (-1.0, -0.2, 0.6)
    ])
    return arrows
