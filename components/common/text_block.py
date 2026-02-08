from __future__ import annotations

from manim import Text

from components.base import Component, ComponentDefaults, _style_get
from schema.scene_plan_models import ObjectSpec


class TextBlock(Component):
    type_name = "TextBlock"

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        text = spec.params.get("text", "")
        font = _style_get(spec, "font", defaults.font)
        font_size = int(_style_get(spec, "font_size", defaults.text_font_size))
        color = _style_get(spec, "color", None)

        kwargs = {"font": font, "font_size": font_size}
        if color is not None:
            kwargs["color"] = color
        return Text(text, **kwargs)

