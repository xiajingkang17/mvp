from manim import *

class TestMath(Scene):
    def construct(self):
        # 测试最基础的数学公式
        tex = MathTex(r"x^2 + y^2 = z^2", color=WHITE).scale(2)
        self.add(tex)
