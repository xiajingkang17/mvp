from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from schema.scene_plan_models import ObjectSpec


@dataclass(frozen=True)
class ComponentDefaults:
    font: str
    text_font_size: int
    bullet_font_size: int
    formula_font_size: int


class Component(ABC):
    type_name: str

    @abstractmethod
    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        raise NotImplementedError


def _style_get(spec: ObjectSpec, key: str, default: Any) -> Any:
    if key in spec.style:
        return spec.style[key]
    return default

