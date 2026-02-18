from __future__ import annotations

from dataclasses import dataclass, field
import math


@dataclass
class Pose:
    x: float
    y: float
    theta: float = 0.0  # degrees
    scale: float = 1.0
    z: float = 0.0

    def copy(self) -> "Pose":
        return Pose(x=self.x, y=self.y, theta=self.theta, scale=self.scale, z=self.z)


@dataclass(frozen=True)
class PartGeometry:
    part_id: str
    anchors: dict[str, tuple[float, float]]

    def anchor_local(self, name: str | None) -> tuple[float, float]:
        key = (name or "center").strip().lower()
        if key in self.anchors:
            return self.anchors[key]
        available = ", ".join(sorted(self.anchors.keys()))
        raise KeyError(f"Unknown anchor '{key}' for part '{self.part_id}'. Available: {available}")


@dataclass(frozen=True)
class ConstraintResidual:
    constraint_id: str
    constraint_type: str
    residual: float
    hard: bool
    satisfied: bool
    detail: str = ""


@dataclass
class SolveResult:
    poses: dict[str, Pose]
    residuals: list[ConstraintResidual] = field(default_factory=list)
    converged: bool = False

    def unsatisfied_hard(self) -> list[ConstraintResidual]:
        return [item for item in self.residuals if item.hard and not item.satisfied]


def rotate_vec(x: float, y: float, theta_deg: float) -> tuple[float, float]:
    rad = math.radians(theta_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return x * c - y * s, x * s + y * c


def anchor_world(pose: Pose, local: tuple[float, float]) -> tuple[float, float]:
    lx, ly = local
    rx, ry = rotate_vec(lx * pose.scale, ly * pose.scale, pose.theta)
    return pose.x + rx, pose.y + ry


def set_center_from_anchor_target(
    pose: Pose,
    local_anchor: tuple[float, float],
    *,
    target_x: float,
    target_y: float,
) -> None:
    rx, ry = rotate_vec(local_anchor[0] * pose.scale, local_anchor[1] * pose.scale, pose.theta)
    pose.x = target_x - rx
    pose.y = target_y - ry
