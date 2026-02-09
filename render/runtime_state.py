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
    objects: dict[str, object] = field(default_factory=dict)  # 对象 id -> Mobject
    visible: set[str] = field(default_factory=set)  # 当前屏幕可见的对象 id
    base_sizes: dict[str, tuple[float, float]] = field(default_factory=dict)  # 对象初始宽高
