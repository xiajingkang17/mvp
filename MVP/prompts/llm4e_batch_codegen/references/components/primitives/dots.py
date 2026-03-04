# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全点与标注点写法。

from manim import *
import numpy as np


def make_point_with_label():
    point = Dot(point=np.array([0.0, 0.0, 0.0]), radius=0.08, color=YELLOW)
    label = Text("P", font_size=28, color=YELLOW).next_to(point, UP + RIGHT, buff=0.08)
    return VGroup(point, label)


def make_particle_marker():
    particle = Dot(point=np.array([0.0, 0.0, 0.0]), radius=0.1, color=YELLOW)
    charge = Text("+q", font_size=24, color=BLACK).move_to(particle.get_center())
    return VGroup(particle, charge)
