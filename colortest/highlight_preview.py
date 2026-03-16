from manim import *

from colortest.ai4learning_theme import (
    AI4LearningBaseScene,
    BLUE_100,
    CYAN_400,
    GREEN_300,
    GREY_200,
    ORANGE_500,
    PURPLE_400,
    RED_500,
    YELLOW_300,
)


class HighlightPreviewScene(AI4LearningBaseScene):
    def construct(self):
        title = self.get_text("Highlight Preview", font_size=34, weight=BOLD)
        subtitle = self.get_text(
            "Check green vs yellow vs brighter purple on the current background",
            color=GREY_200,
            font_size=20,
        )
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.18)

        chips = VGroup(
            self._make_chip("Ice Blue", CYAN_400),
            self._make_chip("Bright Green", GREEN_300),
            self._make_chip("Bright Yellow", YELLOW_300),
            self._make_chip("Warm Orange", ORANGE_500),
            self._make_chip("Bright Purple", PURPLE_400),
            self._make_chip("Coral Red", RED_500),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)

        formula = VGroup(
            self.get_text("Example:", font_size=24, color=GREY_200),
            self.get_text("F", font_size=30, color=RED_500, weight=BOLD),
            self.get_text("=", font_size=24, color=BLUE_100),
            self.get_text("m", font_size=30, color=GREEN_300, weight=BOLD),
            self.get_text("a", font_size=30, color=YELLOW_300, weight=BOLD),
            self.get_text("and", font_size=24, color=GREY_200),
            self.get_text("dx", font_size=30, color=CYAN_400, weight=BOLD),
            self.get_text("pull first", font_size=24, color=GREY_200),
        ).arrange(RIGHT, buff=0.12, aligned_edge=DOWN)

        focus_box = RoundedRectangle(
            corner_radius=0.22,
            width=4.8,
            height=2.3,
            stroke_color=CYAN_400,
            stroke_width=3,
            fill_opacity=0,
        )
        focus_title = self.get_text("Focus First", font_size=24, color=YELLOW_300, weight=BOLD)
        focus_text = self.get_text("Green and yellow separate much more cleanly", font_size=18, color=BLUE_100)
        focus_tag = self.get_text("Purple now reads as contrast", font_size=18, color=PURPLE_400)
        focus_group = VGroup(focus_title, focus_text, focus_tag).arrange(DOWN, buff=0.14)
        focus_group.move_to(focus_box.get_center())

        node_left = Dot(color=GREEN_300, radius=0.12)
        node_mid = Dot(color=YELLOW_300, radius=0.12)
        node_right = Dot(color=RED_500, radius=0.12)
        node_left.move_to(LEFT * 1.85 + DOWN * 1.15)
        node_mid.move_to(ORIGIN + DOWN * 1.15)
        node_right.move_to(RIGHT * 1.85 + DOWN * 1.15)
        arrow_a = Arrow(node_left.get_right(), node_mid.get_left(), buff=0.14, stroke_width=6, color=ORANGE_500)
        arrow_b = Arrow(node_mid.get_right(), node_right.get_left(), buff=0.14, stroke_width=6, color=ORANGE_500)
        arrow_caption = self.get_text("Warm accents stay visible without replacing yellow", font_size=17, color=PURPLE_400)
        arrow_caption.next_to(arrow_a, DOWN, buff=0.24)
        arrow_caption.align_to(arrow_b, RIGHT)

        demo_panel = VGroup(
            focus_box,
            focus_group,
            node_left,
            node_mid,
            node_right,
            arrow_a,
            arrow_b,
            arrow_caption,
        )

        body = VGroup(chips, demo_panel).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        page = VGroup(header, formula, body).arrange(DOWN, buff=0.34)
        self.fit_group(page, max_width=11.9, max_height=5.9)

        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.play(Write(formula), run_time=1.0)
        self.play(
            LaggedStart(*[FadeIn(chip, shift=RIGHT * 0.15) for chip in chips], lag_ratio=0.1),
            run_time=1.2,
        )
        self.play(
            Create(focus_box),
            FadeIn(focus_group, shift=UP * 0.12),
            FadeIn(node_left),
            FadeIn(node_mid),
            FadeIn(node_right),
            GrowArrow(arrow_a),
            GrowArrow(arrow_b),
            FadeIn(arrow_caption, shift=UP * 0.12),
            run_time=1.2,
        )
        self.wait(1.2)

    def _make_chip(self, text, color):
        label = self.get_text(text, font_size=22, color=color, weight=BOLD)
        desc = self.get_text("keyword / formula highlight", font_size=16, color=GREY_200)
        swatch = RoundedRectangle(
            corner_radius=0.16,
            width=0.72,
            height=0.46,
            stroke_width=0,
            fill_color=color,
            fill_opacity=1,
        )
        content = VGroup(label, desc).arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        row = VGroup(swatch, content).arrange(RIGHT, buff=0.22, aligned_edge=UP)
        frame = RoundedRectangle(
            corner_radius=0.18,
            width=row.width + 0.44,
            height=row.height + 0.3,
            stroke_color=color,
            stroke_width=2,
            fill_opacity=0,
        )
        row.move_to(frame.get_center())
        return VGroup(frame, row)
