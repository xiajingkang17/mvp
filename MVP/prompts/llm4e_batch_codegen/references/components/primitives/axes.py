# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全坐标轴写法。
# 物理题默认优先使用无刻度坐标轴，不要生成数学风格的密集刻度线。

from manim import *
import numpy as np


def make_standard_axes():
    x_axis = Arrow(
        np.array([-4.0, 0.0, 0.0]),
        np.array([4.0, 0.0, 0.0]),
        buff=0.0,
        stroke_width=3,
        color=WHITE,
    )
    y_axis = Arrow(
        np.array([0.0, -3.0, 0.0]),
        np.array([0.0, 3.0, 0.0]),
        buff=0.0,
        stroke_width=3,
        color=WHITE,
    )
    labels = VGroup(
        Text("x", font_size=28, color=WHITE).next_to(x_axis.get_end(), RIGHT, buff=0.08),
        Text("y", font_size=28, color=WHITE).next_to(y_axis.get_end(), UP, buff=0.08),
        Text("O", font_size=28, color=WHITE).next_to(ORIGIN, DOWN + LEFT, buff=0.08),
    )
    return VGroup(x_axis, y_axis, labels)


def make_plain_axes_with_origin(origin=np.array([0.0, 0.0, 0.0])):
    x_axis = Arrow(origin + np.array([-3.5, 0.0, 0.0]), origin + np.array([3.5, 0.0, 0.0]), buff=0.0)
    y_axis = Arrow(origin + np.array([0.0, -2.5, 0.0]), origin + np.array([0.0, 2.5, 0.0]), buff=0.0)
    labels = VGroup(
        Text("x", font_size=28).next_to(x_axis.get_end(), RIGHT, buff=0.08),
        Text("y", font_size=28).next_to(y_axis.get_end(), UP, buff=0.08),
        Text("O", font_size=28).next_to(origin, DOWN + LEFT, buff=0.08),
    )
    return VGroup(x_axis, y_axis, labels)
