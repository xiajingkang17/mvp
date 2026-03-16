from pathlib import Path

import numpy as np
from PIL import Image
from manim import *

from .narrated_scene import NarratedScene


A4L_BG = "#0F2748"
A4L_TEXT_MAIN = "#EDF5FF"
A4L_TEXT_SUB = "#D9E7F7"

A4L_BLUE = "#3B82F6"
A4L_PINK = "#F43F5E"
A4L_PURPLE = "#8B5CF6"

PURPLE_200 = "#B1AFCE"
PURPLE_400 = "#E6BEFF"
PURPLE_600 = "#56479C"
PURPLE_900 = "#2C2860"

BLUE_100 = "#D6E2EE"
BLUE_300 = "#7DC7DB"
BLUE_500 = "#4CA4D0"
BLUE_700 = "#0183BB"
BLUE_900 = "#003E52"

CYAN_200 = "#A2CDD4"
CYAN_400 = "#7FDBFF"
CYAN_700 = "#008EB3"

GREEN_100 = "#F0FBC8"
GREEN_300 = "#8EFF5A"
GREEN_500 = "#81C7BC"
GREEN_700 = "#78BBAF"

YELLOW_300 = "#FFF98A"

PINK_200 = "#FFB3B3"
RED_300 = "#FFDBD1"
RED_500 = "#FF3B30"
RED_700 = "#ED746B"

ORANGE_200 = "#FFBEA3"
ORANGE_500 = "#FFB703"
BROWN_700 = "#84491F"

GREY_200 = "#C8C8C8"
GREY_400 = "#9799AA"
GREY_600 = "#8A7A95"
GREY_800 = "#6890A5"

PALETTE = {
    "PURPLE_200": PURPLE_200,
    "PURPLE_400": PURPLE_400,
    "PURPLE_600": PURPLE_600,
    "PURPLE_900": PURPLE_900,
    "BLUE_100": BLUE_100,
    "BLUE_300": BLUE_300,
    "BLUE_500": BLUE_500,
    "BLUE_700": BLUE_700,
    "BLUE_900": BLUE_900,
    "CYAN_200": CYAN_200,
    "CYAN_400": CYAN_400,
    "CYAN_700": CYAN_700,
    "GREEN_100": GREEN_100,
    "GREEN_300": GREEN_300,
    "GREEN_500": GREEN_500,
    "GREEN_700": GREEN_700,
    "YELLOW_300": YELLOW_300,
    "PINK_200": PINK_200,
    "RED_300": RED_300,
    "RED_500": RED_500,
    "RED_700": RED_700,
    "ORANGE_200": ORANGE_200,
    "ORANGE_500": ORANGE_500,
    "BROWN_700": BROWN_700,
    "GREY_200": GREY_200,
    "GREY_400": GREY_400,
    "GREY_600": GREY_600,
    "GREY_800": GREY_800,
}

PALETTE_USAGE_GUIDE = {
    "body_or_formula_base": (
        "BLUE_100",
        "GREY_200",
        "GREY_400",
    ),
    "highlight_text_or_formula_term": (
        "CYAN_400",
        "GREEN_300",
        "YELLOW_300",
        "ORANGE_500",
        "PURPLE_400",
        "RED_500",
    ),
    "shape_structure": (
        "BLUE_300",
        "BLUE_500",
        "CYAN_400",
        "GREEN_500",
        "PURPLE_400",
        "ORANGE_500",
        "RED_500",
    ),
    "soft_note_or_secondary_label": (
        "GREY_400",
        "GREY_600",
        "CYAN_200",
        "GREEN_100",
        "RED_300",
        "ORANGE_200",
    ),
    "avoid_large_body_text": (
        "PURPLE_900",
        "BLUE_900",
        "CYAN_700",
        "BROWN_700",
        "GREY_800",
    ),
    "reserved_for_deep_stroke_or_decor": (
        "PURPLE_900",
        "BLUE_900",
        "CYAN_700",
        "BROWN_700",
        "GREY_800",
    ),
}

PALETTE_USAGE_NOTES = (
    "Use body_or_formula_base for long text and unhighlighted formulas.",
    "Use highlight_text_or_formula_term only for key words or selected formula terms.",
    "Use shape_structure for borders, arrows, nodes, and geometric structure.",
    "Use soft_note_or_secondary_label for muted labels, annotations, and secondary notes.",
    "Do not use avoid_large_body_text for large paragraphs or default formula color.",
)

TEXT_MAIN = A4L_TEXT_MAIN
TEXT_SUB = A4L_TEXT_SUB
TEXT_MUTED = "#AFC0D3"

HL_PRIMARY = CYAN_400
HL_SECONDARY = RED_500
HL_TERTIARY = PURPLE_400
HL_SUCCESS = GREEN_300
HL_ACCENT = YELLOW_300

config.background_color = A4L_BG


class AI4LearningBaseScene(NarratedScene):
    """Shared base scene for AI4Learning videos."""

    default_font = "Microsoft YaHei"
    local_icon_dir = Path(__file__).resolve().parent.parent / "icon"

    def _build_background(self):
        bg_path = Path(__file__).resolve().parent / "pic.png"
        if not bg_path.exists():
            return None

        # Normalize to RGBA before giving the pixels to Manim/Cairo.
        with Image.open(bg_path) as image:
            rgba_pixels = np.array(image.convert("RGBA"))

        bg_image = ImageMobject(rgba_pixels)
        bg_image.scale_to_fit_width(config.frame_width)
        if bg_image.height < config.frame_height:
            bg_image.scale_to_fit_height(config.frame_height)
        bg_image.move_to(ORIGIN)
        bg_image.set_z_index(-100)

        # Darken and unify the texture so light text and formulas stay legible.
        bg_tint = Rectangle(
            width=config.frame_width,
            height=config.frame_height,
            stroke_width=0,
            fill_color=A4L_BG,
            fill_opacity=0.58,
        )
        bg_tint.move_to(ORIGIN)
        bg_tint.set_z_index(-90)
        return Group(bg_image, bg_tint)

    def setup(self):
        super().setup()
        self._bg_image = self._build_background()
        if self._bg_image is not None:
            self.add(self._bg_image)

    def get_persistent_mobjects(self):
        bg_image = getattr(self, "_bg_image", None)
        return [bg_image] if bg_image is not None else []

    def clear_scene_keep_bg(self, run_time=0.7, wait_time=0.3):
        persistent = self.get_persistent_mobjects()
        to_fade = [
            mob
            for mob in self.mobjects
            if all(mob is not keep for keep in persistent)
        ]
        if to_fade:
            self.play(FadeOut(Group(*to_fade)), run_time=run_time)
        self._subtitle_mob = None
        self._section_badge = None
        self._section_badge_text = None
        self.wait(wait_time)

    def get_local_icon_path(self, filename):
        requested = Path(str(filename)).name.strip()
        if not requested:
            raise ValueError("Local icon filename is empty")

        icon_dir = Path(self.local_icon_dir)
        exact_path = icon_dir / requested
        if exact_path.exists():
            return exact_path

        requested_lower = requested.lower()
        requested_stem = Path(requested).stem.lower()
        stem_matches = []
        for candidate in icon_dir.iterdir():
            if not candidate.is_file():
                continue
            candidate_name = candidate.name.lower()
            if candidate_name == requested_lower:
                return candidate
            if candidate.stem.lower() == requested_stem:
                stem_matches.append(candidate)

        if len(stem_matches) == 1:
            return stem_matches[0]

        raise FileNotFoundError(f"Local icon not found: {requested}")

    def load_local_icon(self, filename, height=0.9, width=None, **kwargs):
        path = self.get_local_icon_path(filename)
        if path.suffix.lower() == ".svg":
            icon = SVGMobject(str(path), **kwargs)
        else:
            icon = ImageMobject(str(path), **kwargs)
        if height is not None:
            icon.scale_to_fit_height(height)
        if width is not None:
            icon.scale_to_fit_width(width)
        return icon

    def get_text(self, string, color=A4L_TEXT_MAIN, font_size=36, **kwargs):
        font = kwargs.pop("font", getattr(self, "default_font", "Microsoft YaHei"))
        return Text(string, color=color, font=font, font_size=font_size, **kwargs)

    def get_math(self, string, color=A4L_TEXT_MAIN, font_size=48, **kwargs):
        return MathTex(string, color=color, font_size=font_size, **kwargs)

    def get_highlighted_math(self, string, color=A4L_BLUE, font_size=48, **kwargs):
        return MathTex(string, color=color, font_size=font_size, **kwargs)
