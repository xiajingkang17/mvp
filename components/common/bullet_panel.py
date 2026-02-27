from __future__ import annotations

from manim import DOWN, LEFT, VGroup, Text

from components.base import Component, ComponentDefaults, _style_get, resolve_text_font
from schema.scene_plan_models import ObjectSpec


class BulletPanel(Component):
    type_name = "BulletPanel"

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        items = spec.params.get("items", []) or []
        if not isinstance(items, list):
            items = [str(items)]

        font = resolve_text_font(str(_style_get(spec, "font", defaults.font)))
        font_size = int(_style_get(spec, "font_size", defaults.bullet_font_size))
        color = _style_get(spec, "color", None)

        lines = []
        for item in items:
            kwargs = {"font": font, "font_size": font_size}
            if color is not None:
                kwargs["color"] = color
            lines.append(Text(f"- {item}", **kwargs))

        group = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        return group
