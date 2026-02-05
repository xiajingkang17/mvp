from __future__ import annotations

from manim import MathTex

from components.base import Component, ComponentDefaults, _style_get
from schema.scene_plan_models import ObjectSpec


class Formula(Component):
    type_name = "Formula"

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        latex = spec.params.get("latex")
        if latex is None:
            latex = spec.params.get("content", "")

        font_size = int(_style_get(spec, "font_size", defaults.formula_font_size))
        color = _style_get(spec, "color", None)

        mobj = MathTex(latex, font_size=font_size)
        if color is not None:
            mobj.set_color(color)
        return mobj

