from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.config import AppConfig, RenderDefaults


@dataclass(frozen=True)
class RenderContext:
    app: AppConfig
    frame_width: float
    frame_height: float

    @property
    def defaults(self) -> RenderDefaults:
        return self.app.defaults


@dataclass
class RuntimeState:
    objects: dict[str, object] = field(default_factory=dict)  # object id -> Mobject
    visible: set[str] = field(default_factory=set)  # currently visible object ids
    base_sizes: dict[str, tuple[float, float]] = field(default_factory=dict)  # object initial (w,h)
    timeline_seconds: float = 0.0
    timeline_clock: object | None = None
