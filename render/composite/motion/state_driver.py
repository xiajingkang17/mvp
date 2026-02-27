from __future__ import annotations

import math
from typing import Any

from schema.composite_graph_models import GraphMotion

from ..types import Pose
from .common import _arg, _to_bool, _to_float, _to_float_or_none
from .timeline import evaluate_timeline, timeline_bounds

_END_CONDITION_METRIC_ALIASES = {
    "x": "x",
    "y": "y",
    "dx": "dx",
    "dy": "dy",
    "delta_x": "dx",
    "delta_y": "dy",
    "tau": "tau",
}
_END_CONDITION_OPS = {">=", "<="}


def _model_params_dict(args: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    model = args.get("model")
    if not isinstance(model, dict):
        return "", {}
    kind = str(model.get("kind", "")).strip().lower()
    params = model.get("params")
    if not isinstance(params, dict):
        params = {}
    return kind, dict(params)


def _resolve_param(
    params: dict[str, Any],
    handoff_state: dict[str, float] | None,
    key: str,
    default: float | None = None,
) -> float | None:
    value = params.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    if handoff_state is not None and key in handoff_state and isinstance(handoff_state.get(key), (int, float)):
        return float(handoff_state[key])
    return default


def _resolve_theta(
    *,
    args: dict[str, Any],
    current_theta: float,
    vx: float | None,
    vy: float | None,
) -> float:
    orient_mode = str(_arg(args, "orient_mode", "theta_mode", "orient", default="keep")).strip().lower()
    angle_offset = _to_float(_arg(args, "angle_offset", default=0.0), default=0.0)
    if orient_mode in {"tangent", "velocity_tangent"}:
        if vx is None or vy is None:
            return float(current_theta) + float(angle_offset)
        speed = math.hypot(float(vx), float(vy))
        if speed <= 1e-9:
            return float(current_theta) + float(angle_offset)
        return math.degrees(math.atan2(float(vy), float(vx))) + float(angle_offset)
    if orient_mode == "fixed":
        return _to_float(_arg(args, "theta", "angle", default=current_theta), default=float(current_theta)) + float(
            angle_offset
        )
    if "theta" in args or "angle" in args:
        return _to_float(_arg(args, "theta", "angle", default=current_theta), default=float(current_theta)) + float(
            angle_offset
        )
    return float(current_theta) + float(angle_offset)


def _parse_sampled_path_2d_samples(params: dict[str, Any]) -> list[tuple[float, float, float]]:
    raw = params.get("samples")
    if not isinstance(raw, list):
        return []
    parsed: list[tuple[float, float, float]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        tau = _to_float_or_none(item.get("tau"))
        x = _to_float_or_none(item.get("x"))
        y = _to_float_or_none(item.get("y"))
        if tau is None or x is None or y is None:
            continue
        parsed.append((float(tau), float(x), float(y)))
    parsed.sort(key=lambda point: point[0])
    return parsed


def _evaluate_sampled_path_2d(
    samples: list[tuple[float, float, float]],
    tau: float,
) -> tuple[float, float, float, float] | None:
    if len(samples) < 2:
        return None

    value = float(tau)
    if value <= samples[0][0]:
        tau0, x0, y0 = samples[0]
        tau1, x1, y1 = samples[1]
        denom = float(tau1 - tau0)
        if abs(denom) <= 1e-9:
            return float(x0), float(y0), 0.0, 0.0
        return float(x0), float(y0), float((x1 - x0) / denom), float((y1 - y0) / denom)

    if value >= samples[-1][0]:
        tau0, x0, y0 = samples[-2]
        tau1, x1, y1 = samples[-1]
        denom = float(tau1 - tau0)
        if abs(denom) <= 1e-9:
            return float(x1), float(y1), 0.0, 0.0
        return float(x1), float(y1), float((x1 - x0) / denom), float((y1 - y0) / denom)

    for index in range(1, len(samples)):
        tau0, x0, y0 = samples[index - 1]
        tau1, x1, y1 = samples[index]
        if value > tau1:
            continue
        denom = float(tau1 - tau0)
        if abs(denom) <= 1e-9:
            return float(x1), float(y1), 0.0, 0.0
        alpha = (value - tau0) / denom
        x = float(x0 + (x1 - x0) * alpha)
        y = float(y0 + (y1 - y0) * alpha)
        vx = float((x1 - x0) / denom)
        vy = float((y1 - y0) / denom)
        return x, y, vx, vy

    return float(samples[-1][1]), float(samples[-1][2]), 0.0, 0.0


def parse_state_driver_end_condition(args: dict[str, Any]) -> dict[str, Any] | None:
    raw = args.get("end_condition")
    if not isinstance(raw, dict):
        return None

    metric_raw = _arg(raw, "metric", "key", "axis", default="")
    metric = _END_CONDITION_METRIC_ALIASES.get(str(metric_raw).strip().lower())
    op = str(raw.get("op", "")).strip()
    value = raw.get("value")
    if metric is None or op not in _END_CONDITION_OPS or not isinstance(value, (int, float)):
        return None
    return {"metric": metric, "op": op, "value": float(value)}


def _metric_value_for_end_condition(
    *,
    metric: str,
    target: dict[str, float],
    start_target: dict[str, float],
    tau: float,
) -> float | None:
    if metric == "x":
        return float(target.get("x"))
    if metric == "y":
        return float(target.get("y"))
    if metric == "dx":
        return float(target.get("x")) - float(start_target.get("x"))
    if metric == "dy":
        return float(target.get("y")) - float(start_target.get("y"))
    if metric == "tau":
        return float(tau)
    return None


def _eval_end_condition(
    *,
    metric_value: float,
    op: str,
    threshold: float,
) -> bool:
    if op == ">=":
        return float(metric_value) >= float(threshold)
    return float(metric_value) <= float(threshold)


def find_state_driver_end_event(
    motion: GraphMotion,
    *,
    current_pose: Pose | None = None,
    handoff_state: dict[str, float] | None = None,
    sample_steps: int = 180,
) -> dict[str, Any] | None:
    args = dict(motion.args or {})
    condition = parse_state_driver_end_condition(args)
    if condition is None:
        return None

    bounds = timeline_bounds(motion.timeline)
    if bounds is None:
        return None
    start_t, end_t = bounds
    if float(end_t) <= float(start_t) + 1e-9:
        return None

    param_key = str(_arg(args, "param_key", default="tau")).strip() or "tau"
    start_target = evaluate_state_driver_target(
        motion,
        time_value=float(start_t),
        current_pose=current_pose,
        handoff_state=handoff_state,
    )
    if start_target is None:
        return None

    metric = str(condition["metric"])
    op = str(condition["op"])
    threshold = float(condition["value"])

    def _eval(time_point: float) -> tuple[bool, float, dict[str, float]] | None:
        target = evaluate_state_driver_target(
            motion,
            time_value=float(time_point),
            current_pose=current_pose,
            handoff_state=handoff_state,
        )
        if target is None:
            return None
        tau = evaluate_timeline(motion.timeline, float(time_point), key=param_key)
        metric_value = _metric_value_for_end_condition(
            metric=metric,
            target=target,
            start_target=start_target,
            tau=tau,
        )
        if metric_value is None:
            return None
        return _eval_end_condition(metric_value=metric_value, op=op, threshold=threshold), float(metric_value), target

    start_eval = _eval(float(start_t))
    if start_eval is None:
        return None
    if start_eval[0]:
        return {
            "time": float(start_t),
            "metric": metric,
            "op": op,
            "value": threshold,
            "metric_value": float(start_eval[1]),
            "target": dict(start_eval[2]),
        }

    prev_t = float(start_t)
    prev_eval = start_eval
    steps = max(16, int(sample_steps))
    span = float(end_t) - float(start_t)
    hit_t: float | None = None
    hit_eval: tuple[bool, float, dict[str, float]] | None = None

    for index in range(1, steps + 1):
        time_point = float(start_t) + span * (float(index) / float(steps))
        curr_eval = _eval(time_point)
        if curr_eval is None:
            continue
        if curr_eval[0]:
            if not prev_eval[0]:
                low_t = prev_t
                high_t = float(time_point)
                high_eval = curr_eval
                for _ in range(28):
                    if high_t - low_t <= 1e-6:
                        break
                    mid_t = 0.5 * (low_t + high_t)
                    mid_eval = _eval(mid_t)
                    if mid_eval is None:
                        break
                    if mid_eval[0]:
                        high_t = mid_t
                        high_eval = mid_eval
                    else:
                        low_t = mid_t
                hit_t = float(high_t)
                hit_eval = high_eval
            else:
                hit_t = float(time_point)
                hit_eval = curr_eval
            break
        prev_t = float(time_point)
        prev_eval = curr_eval

    if hit_t is None or hit_eval is None:
        return None

    return {
        "time": float(hit_t),
        "metric": metric,
        "op": op,
        "value": threshold,
        "metric_value": float(hit_eval[1]),
        "target": dict(hit_eval[2]),
    }


def evaluate_state_driver_target(
    motion: GraphMotion,
    *,
    time_value: float,
    current_pose: Pose | None = None,
    handoff_state: dict[str, float] | None = None,
) -> dict[str, float] | None:
    args = dict(motion.args or {})
    mode = str(_arg(args, "mode", default="model")).strip().lower()
    if mode != "model":
        return None

    bounds = timeline_bounds(motion.timeline)
    if bounds is None:
        return None
    start_t, end_t = bounds
    if float(time_value) + 1e-9 < float(start_t):
        return None
    hold_after = _to_bool(_arg(args, "hold_after", default=True), True)
    if float(time_value) - 1e-9 > float(end_t) and not hold_after:
        return None

    param_key = str(_arg(args, "param_key", default="tau")).strip() or "tau"
    tau = evaluate_timeline(motion.timeline, time_value, key=param_key)
    kind, params = _model_params_dict(args)
    if not kind:
        return None

    part_id = str(_arg(args, "part_id", default="")).strip()
    if not part_id:
        return None

    current_theta = float(current_pose.theta) if current_pose is not None else 0.0

    if kind == "ballistic_2d":
        x0 = _resolve_param(params, handoff_state, "x0")
        y0 = _resolve_param(params, handoff_state, "y0")
        vx0 = _resolve_param(params, handoff_state, "vx0")
        vy0 = _resolve_param(params, handoff_state, "vy0")
        if x0 is None or y0 is None or vx0 is None or vy0 is None:
            return None
        g = _resolve_param(params, handoff_state, "g", 9.8)
        if g is None:
            g = 9.8
        x = float(x0) + float(vx0) * float(tau)
        y = float(y0) + float(vy0) * float(tau) - 0.5 * float(g) * float(tau) * float(tau)
        vx = float(vx0)
        vy = float(vy0) - float(g) * float(tau)
        orient_args = args
        has_orient_override = any(key in args for key in ("orient_mode", "theta_mode", "orient", "theta", "angle"))
        if not has_orient_override:
            # Default for ballistic blocks/carts in teaching scenes:
            # keep horizontal unless explicitly overridden in motion args.
            orient_args = dict(args)
            orient_args["orient_mode"] = "fixed"
            orient_args["theta"] = 0.0
        theta = _resolve_theta(args=orient_args, current_theta=current_theta, vx=vx, vy=vy)
        return {"part_id": part_id, "x": x, "y": y, "theta": theta, "vx": vx, "vy": vy}

    if kind == "uniform_circular_2d":
        cx = _resolve_param(params, handoff_state, "cx")
        cy = _resolve_param(params, handoff_state, "cy")
        r = _resolve_param(params, handoff_state, "r")
        omega = _resolve_param(params, handoff_state, "omega")
        if cx is None or cy is None or r is None or omega is None:
            return None
        phi0 = _resolve_param(params, handoff_state, "phi0", 0.0)
        if phi0 is None:
            phi0 = 0.0
        angle = float(phi0) + float(omega) * float(tau)
        x = float(cx) + float(r) * math.cos(angle)
        y = float(cy) + float(r) * math.sin(angle)
        vx = -float(r) * float(omega) * math.sin(angle)
        vy = float(r) * float(omega) * math.cos(angle)
        theta = _resolve_theta(args=args, current_theta=current_theta, vx=vx, vy=vy)
        return {"part_id": part_id, "x": x, "y": y, "theta": theta, "vx": vx, "vy": vy}

    if kind == "sampled_path_2d":
        samples = _parse_sampled_path_2d_samples(params)
        evaluated = _evaluate_sampled_path_2d(samples, float(tau))
        if evaluated is None:
            return None
        x, y, vx, vy = evaluated
        theta = _resolve_theta(args=args, current_theta=current_theta, vx=vx, vy=vy)
        return {"part_id": part_id, "x": x, "y": y, "theta": theta, "vx": vx, "vy": vy}

    return None


__all__ = [
    "evaluate_state_driver_target",
    "find_state_driver_end_event",
    "parse_state_driver_end_condition",
]
