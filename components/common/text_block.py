from __future__ import annotations

from manim import DOWN, LEFT, RIGHT, MathTex, Text, VGroup

from components.base import Component, ComponentDefaults, _style_get, resolve_text_font
from components.common.inline_math import split_inline_math_segments
from schema.scene_plan_models import ObjectSpec


class TextBlock(Component):
    type_name = "TextBlock"

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        text = spec.params.get("text")
        if text is None:
            text = spec.params.get("content", "")
        text = str(text)
        font = resolve_text_font(str(_style_get(spec, "font", defaults.font)))
        font_size = int(_style_get(spec, "font_size", defaults.text_font_size))
        color = _style_get(spec, "color", None)

        kwargs = {"font": font, "font_size": font_size}
        if color is not None:
            kwargs["color"] = color

        if "$" not in text:
            return Text(text, **kwargs)

        lines = text.splitlines()
        if not lines:
            lines = [""]

        rendered_lines = [self._render_inline_mixed_line(line, kwargs=kwargs, font_size=font_size, color=color) for line in lines]
        if len(rendered_lines) == 1:
            return rendered_lines[0]

        group = VGroup(*rendered_lines)
        group.arrange(DOWN, aligned_edge=LEFT, buff=max(0.12, font_size * 0.004))
        return group

    @staticmethod
    def _render_inline_mixed_line(
        line: str,
        *,
        kwargs: dict,
        font_size: int,
        color,
    ):
        segments = split_inline_math_segments(line)
        parts = []
        for kind, value in segments:
            if not value:
                continue

            if kind == "math":
                expression = value.strip()
                if not expression:
                    continue
                try:
                    mobj = MathTex(expression, font_size=font_size)
                    if color is not None:
                        mobj.set_color(color)
                    parts.append(mobj)
                    continue
                except Exception:  # noqa: BLE001
                    # Fall back to plain text so one bad formula doesn't break the whole scene.
                    parts.append(Text(f"${value}$", **kwargs))
                    continue

            parts.append(Text(value, **kwargs))

        if not parts:
            empty = Text(" ", **kwargs)
            empty.set_opacity(0.0)
            return empty

        line_group = VGroup(*parts)
        line_group.arrange(RIGHT, aligned_edge=DOWN, buff=max(0.04, font_size * 0.0015))
        return line_group

