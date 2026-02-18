from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from components.base import Component, ComponentDefaults, _style_get
from schema.scene_plan_models import ObjectSpec

from .electricity import Battery, Bulb, Capacitor, Resistor, Switch
from .electromagnetism import (
    Ammeter,
    Battery as EMBatteryClass,
    Capacitor as EMCapacitorClass,
    Inductor,
    LED,
    LightBulb,
    Potentiometer,
    Rheostat,
    Switch as EMSwitchClass,
    Voltmeter,
)
from .mechanics import (
    Block,
    Cart,
    CircularGroove,
    ArcTrack,
    FixedPulley,
    Hinge,
    InclinedPlaneGroup,
    MovablePulley,
    Pulley,
    QuarterCart,
    QuarterCircleGroove,
    Rod,
    Rope,
    SemicircleCart,
    SemicircleGroove,
    Spring,
    SpringScale,
    Wall,
    Weight,
)
from .specs import PHYSICS_OBJECT_PARAM_SPECS


@dataclass(frozen=True)
class PhysicsObjectDef:
    object_type: str
    builder: Callable


PHYSICS_OBJECT_DEFS: tuple[PhysicsObjectDef, ...] = (
    # Mechanics
    PhysicsObjectDef("InclinedPlaneGroup", InclinedPlaneGroup),
    PhysicsObjectDef("Wall", Wall),
    PhysicsObjectDef("Block", Block),
    PhysicsObjectDef("Cart", Cart),
    PhysicsObjectDef("Weight", Weight),
    PhysicsObjectDef("Pulley", Pulley),
    PhysicsObjectDef("FixedPulley", FixedPulley),
    PhysicsObjectDef("MovablePulley", MovablePulley),
    PhysicsObjectDef("Rope", Rope),
    PhysicsObjectDef("Spring", Spring),
    PhysicsObjectDef("Rod", Rod),
    PhysicsObjectDef("Hinge", Hinge),
    PhysicsObjectDef("CircularGroove", CircularGroove),
    PhysicsObjectDef("ArcTrack", ArcTrack),
    PhysicsObjectDef("SemicircleGroove", SemicircleGroove),
    PhysicsObjectDef("QuarterCircleGroove", QuarterCircleGroove),
    PhysicsObjectDef("SemicircleCart", SemicircleCart),
    PhysicsObjectDef("QuarterCart", QuarterCart),
    PhysicsObjectDef("SpringScale", SpringScale),
    # Electricity / electromagnetism
    PhysicsObjectDef("Resistor", Resistor),
    PhysicsObjectDef("Battery", Battery),
    PhysicsObjectDef("Bulb", Bulb),
    PhysicsObjectDef("Switch", Switch),
    PhysicsObjectDef("Capacitor", Capacitor),
    PhysicsObjectDef("EMBattery", EMBatteryClass),
    PhysicsObjectDef("EMSwitch", EMSwitchClass),
    PhysicsObjectDef("Ammeter", Ammeter),
    PhysicsObjectDef("Voltmeter", Voltmeter),
    PhysicsObjectDef("LightBulb", LightBulb),
    PhysicsObjectDef("EMCapacitor", EMCapacitorClass),
    PhysicsObjectDef("Rheostat", Rheostat),
    PhysicsObjectDef("Potentiometer", Potentiometer),
    PhysicsObjectDef("Inductor", Inductor),
    PhysicsObjectDef("LED", LED),
)


class PhysicsObjectComponent(Component):
    def __init__(self, object_type: str, builder: Callable):
        self.type_name = object_type
        self._builder = builder
        self._allowed_params = set(PHYSICS_OBJECT_PARAM_SPECS.get(object_type, ()))

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        params = dict(spec.params or {})
        if "color" in self._allowed_params and "color" not in params:
            style_color = _style_get(spec, "color", None)
            if style_color is not None:
                params["color"] = style_color

        unknown = sorted(k for k in params if k not in self._allowed_params)
        if unknown:
            raise ValueError(f"{self.type_name} has unknown params: {', '.join(unknown)}")

        return self._builder(**params)


def build_physics_components() -> dict[str, Component]:
    return {
        item.object_type: PhysicsObjectComponent(item.object_type, item.builder)
        for item in PHYSICS_OBJECT_DEFS
    }
