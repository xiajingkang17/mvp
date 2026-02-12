from __future__ import annotations

from dataclasses import dataclass

from components.base import Component, ComponentDefaults
from components.composite.object_component import CompositeObjectComponent
from components.common.bullet_panel import BulletPanel
from components.common.formula import Formula
from components.common.text_block import TextBlock
from components.physics.object_components import build_physics_components
from schema.scene_plan_models import ObjectSpec


@dataclass(frozen=True)
class ComponentRegistry:
    components: dict[str, Component]

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        component = self.components.get(spec.type)
        if not component:
            raise KeyError(f"Unknown component type: {spec.type}")
        return component.build(spec, defaults=defaults)


DEFAULT_REGISTRY = ComponentRegistry(
    components={
        TextBlock.type_name: TextBlock(),
        BulletPanel.type_name: BulletPanel(),
        Formula.type_name: Formula(),
        CompositeObjectComponent.type_name: CompositeObjectComponent(),
        **build_physics_components(),
    }
)

