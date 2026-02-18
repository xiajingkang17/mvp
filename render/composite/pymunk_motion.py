from __future__ import annotations

import hashlib
import json
from typing import Any

from schema.composite_graph_models import GraphMotion


class PymunkNotAvailable(RuntimeError):
    pass


_CACHE: dict[str, list[dict[str, Any]]] = {}


def _cache_key(motion: GraphMotion) -> str:
    payload = {"id": motion.id, "type": motion.type, "args": motion.args}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def precompute_timeline(motion: GraphMotion) -> list[dict[str, Any]]:
    """
    Build a dense timeline for a single body and return a list of points:
      {"t": float, "x": float, "y": float, "theta": float}

    Supported motion types:
    - "pymunk_body": rigid body with optional constant force/impulse and gravity.
    """
    if motion.type != "pymunk_body":
        return []

    key = _cache_key(motion)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    try:
        import pymunk  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise PymunkNotAvailable(
            "Motion type 'pymunk_body' requires pymunk. Install with: pip install pymunk"
        ) from exc

    args = dict(motion.args or {})

    duration = float(args.get("duration", 2.0))
    fps = float(args.get("fps", 60.0))
    substeps = int(args.get("substeps", 2))
    if duration <= 0:
        _CACHE[key] = []
        return []
    if fps <= 0:
        fps = 60.0
    substeps = max(1, substeps)

    gravity = args.get("gravity", [0.0, -9.8])
    try:
        gx, gy = float(gravity[0]), float(gravity[1])
    except Exception:  # noqa: BLE001
        gx, gy = 0.0, -9.8

    space = pymunk.Space()
    space.gravity = (gx, gy)

    mass = float(args.get("mass", 1.0))
    moment = args.get("moment")
    if moment is None:
        # Default: treat as a point mass.
        moment = pymunk.moment_for_circle(mass, 0.0, 0.01)
    moment = float(moment)

    body = pymunk.Body(mass, moment)
    body.position = (float(args.get("x0", 0.0)), float(args.get("y0", 0.0)))
    body.velocity = (float(args.get("vx0", 0.0)), float(args.get("vy0", 0.0)))
    body.angle = float(args.get("theta0", 0.0))
    body.angular_velocity = float(args.get("omega0", 0.0))

    # Optional: simple circle shape for collisions if segments are provided later.
    radius = float(args.get("radius", 0.01))
    shape = pymunk.Circle(body, radius)
    shape.elasticity = float(args.get("elasticity", 0.0))
    shape.friction = float(args.get("friction", 0.0))
    space.add(body, shape)

    # Optional constant force applied each step: [fx, fy]
    force = args.get("force")
    try:
        fx, fy = float(force[0]), float(force[1]) if isinstance(force, (list, tuple)) else (0.0, 0.0)
    except Exception:  # noqa: BLE001
        fx, fy = 0.0, 0.0

    # Optional one-time impulse at t=0: [jx, jy]
    impulse = args.get("impulse")
    if isinstance(impulse, (list, tuple)) and len(impulse) >= 2:
        try:
            body.apply_impulse_at_local_point((float(impulse[0]), float(impulse[1])))
        except Exception:  # noqa: BLE001
            pass

    dt = 1.0 / fps
    step_dt = dt / substeps
    frames = int(duration * fps) + 1

    out: list[dict[str, Any]] = []
    t = 0.0
    for _ in range(frames):
        out.append({"t": float(t), "x": float(body.position.x), "y": float(body.position.y), "theta": float(body.angle)})
        for _s in range(substeps):
            if fx != 0.0 or fy != 0.0:
                body.force = (fx, fy)
            space.step(step_dt)
        t += dt

    _CACHE[key] = out
    return out

