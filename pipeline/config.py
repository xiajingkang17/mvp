from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "configs"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class SafeArea:
    left: float
    right: float
    top: float
    bottom: float


@dataclass(frozen=True)
class RenderDefaults:
    font: str
    text_font_size: int
    bullet_font_size: int
    formula_font_size: int
    action_duration: float


@dataclass(frozen=True)
class AppConfig:
    safe_area: SafeArea
    slot_padding: float
    defaults: RenderDefaults
    frame_width: float
    frame_height: float


def load_app_config(path: Path | None = None) -> AppConfig:
    path = path or (CONFIG_DIR / "app.yaml")
    raw = load_yaml(path) or {}

    render = raw.get("render", {})
    safe = render.get("safe_area", {})
    defaults = render.get("defaults", {})
    frame = raw.get("frame", {})

    safe_area = SafeArea(
        left=float(safe.get("left", 0.05)),
        right=float(safe.get("right", 0.05)),
        top=float(safe.get("top", 0.05)),
        bottom=float(safe.get("bottom", 0.05)),
    )

    render_defaults = RenderDefaults(
        font=str(defaults.get("font", "Arial")),
        text_font_size=int(defaults.get("text_font_size", 36)),
        bullet_font_size=int(defaults.get("bullet_font_size", 34)),
        formula_font_size=int(defaults.get("formula_font_size", 48)),
        action_duration=float(defaults.get("action_duration", 1.0)),
    )

    return AppConfig(
        safe_area=safe_area,
        slot_padding=float(render.get("slot_padding", 0.05)),
        defaults=render_defaults,
        frame_width=float(frame.get("width", 14.222)),
        frame_height=float(frame.get("height", 8.0)),
    )


def load_enums(path: Path | None = None) -> dict[str, set[str]]:
    path = path or (CONFIG_DIR / "enums.yaml")
    raw = load_yaml(path) or {}
    return {
        "object_types": set(raw.get("object_types", []) or []),
        "layout_types": set(raw.get("layout_types", []) or []),
        "action_ops": set(raw.get("action_ops", []) or []),
        "anims": set(raw.get("anims", []) or []),
    }

