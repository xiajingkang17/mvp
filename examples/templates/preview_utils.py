from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_root_on_syspath(file: str) -> None:
    root_dir = Path(file).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))


def add_template_preview(scene, template_type: str) -> None:
    from manim import BLUE, GRAY, WHITE, YELLOW, UP, Rectangle, Text, VGroup, config

    from layout.engine import Frame, SafeArea, compute_placements
    from layout.templates import TEMPLATE_REGISTRY
    from pipeline.config import load_app_config

    app = load_app_config()
    safe = SafeArea(
        left=app.safe_area.left,
        right=app.safe_area.right,
        top=app.safe_area.top,
        bottom=app.safe_area.bottom,
    )
    frame = Frame(width=float(config.frame_width), height=float(config.frame_height))

    template = TEMPLATE_REGISTRY[template_type]
    slot_map = {slot_id: slot_id for slot_id in template.slots.keys()}
    placements = compute_placements(template_type, slot_map, safe_area=safe, frame=frame)

    title = Text(f"模板预览：{template_type}", font_size=36, color=WHITE).to_edge(UP)

    frame_border = Rectangle(width=frame.width, height=frame.height, color=GRAY).set_stroke(width=2)
    safe_w = frame.width * (1.0 - safe.left - safe.right)
    safe_h = frame.height * (1.0 - safe.top - safe.bottom)
    safe_border = Rectangle(width=safe_w, height=safe_h, color=GRAY).set_stroke(width=2)

    group = VGroup(frame_border, safe_border)
    for slot_id, placement in placements.items():
        outer = Rectangle(width=placement.width, height=placement.height, color=YELLOW).set_stroke(width=3)
        outer.move_to([placement.center_x, placement.center_y, 0])

        inner_w = max(0.01, placement.width * (1 - 2 * app.slot_padding))
        inner_h = max(0.01, placement.height * (1 - 2 * app.slot_padding))
        inner = Rectangle(width=inner_w, height=inner_h, color=BLUE).set_stroke(width=2)
        inner.move_to([placement.center_x, placement.center_y, 0])

        label = Text(slot_id, font_size=24, color=WHITE).move_to(outer.get_center())
        group.add(outer, inner, label)

    scene.add(title, group)
    scene.wait(2)
