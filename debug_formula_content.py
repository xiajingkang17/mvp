from manim import *
import sys
sys.path.insert(0, '/Users/chenshutong/Desktop/mvp/mvp/mvp-main')

from schema.scene_plan_models import ObjectSpec
from components.common.formula import Formula
from components.base import ComponentDefaults

class TestFormulaContent(Scene):
    def construct(self):
        # 测试使用 "latex" 参数（原始代码）
        print("=== Test 1: Using 'latex' parameter ===")
        spec1 = ObjectSpec(
            type="Formula",
            params={"latex": r"x^2 + y^2 = z^2"},
            style={"fontSize": 48, "color": "#FFFFFF"}
        )
        defaults = ComponentDefaults(
            font="Arial",
            text_font_size=36,
            bullet_font_size=24,
            formula_font_size=48
        )

        formula1 = Formula().build(spec1, defaults=defaults)
        print(f"Formula1 built: {formula1}")
        print(f"Formula1 text: {formula1.latex if hasattr(formula1, 'latex') else 'N/A'}")

        # 测试使用 "content" 参数（scene_plan.json 中的方式）
        print("\n=== Test 2: Using 'content' parameter ===")
        spec2 = ObjectSpec(
            type="Formula",
            params={"content": r"x + 2 = 5"},
            style={"fontSize": 48, "color": "#FFFFFF"}
        )

        formula2 = Formula().build(spec2, defaults=defaults)
        print(f"Formula2 built: {formula2}")
        print(f"Formula2 text: {formula2.latex if hasattr(formula2, 'latex') else 'N/A'}")

        # 显示在屏幕上
        formula1.shift(UP * 2)
        formula2.shift(DOWN * 2)

        self.add(formula1)
        self.add(Text("Using 'latex' param", font_size=24).next_to(formula1, DOWN))

        self.add(formula2)
        self.add(Text("Using 'content' param", font_size=24).next_to(formula2, DOWN))
