# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全磁场叉号写法。
# 不要使用 Cross(point) 或 Cross(size=...)。

from manim import *
import numpy as np


def make_cross_marker(center):
    diag_1 = Line(
        center + np.array([-0.12, -0.12, 0.0]),
        center + np.array([0.12, 0.12, 0.0]),
        color=GREEN,
        stroke_width=3,
    )
    diag_2 = Line(
        center + np.array([-0.12, 0.12, 0.0]),
        center + np.array([0.12, -0.12, 0.0]),
        color=GREEN,
        stroke_width=3,
    )
    return VGroup(diag_1, diag_2)


def make_cross_array():
    centers = [
        np.array([-1.0, -0.4, 0.0]),
        np.array([-0.3, -0.4, 0.0]),
        np.array([-1.0, -1.0, 0.0]),
        np.array([-0.3, -1.0, 0.0]),
    ]
    return VGroup(*[make_cross_marker(center) for center in centers])
