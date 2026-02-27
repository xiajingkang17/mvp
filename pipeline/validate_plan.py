from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from layout.params import sanitize_params
from layout.templates import TEMPLATE_REGISTRY
from schema.composite_graph_models import CompositeGraph
from schema.scene_plan_models import PlayAction, ScenePlan, WaitAction

from components.common.inline_math import (
    has_latex_tokens_outside_inline_math,
    has_unbalanced_inline_math_delimiters,
)
from components.common.latex_subscripts import (
    shorten_inline_math_subscripts,
    shorten_latex_subscripts,
)
from components.physics.specs import PHYSICS_OBJECT_PARAM_SPECS
from llm_constraints.constraints_spec import validate_constraint_args
from .config import load_app_config, load_enums


@dataclass(frozen=True)
class ValidationErrorItem:
    message: str


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_ARC_ID_HINT_RE = re.compile(r"(?:^|_)(arc|semicircle|curve)(?:_|$)")
_CURVED_PART_TYPES = {"ArcTrack", "SemicircleGroove", "QuarterCircleGroove", "CircularGroove"}
_PROJECTILE_HORIZONTAL_PART_TYPES = {"Block", "Cart"}
_ALLOWED_LAYOUT_ANCHORS = {"C", "U", "D", "L", "R", "UL", "UR", "DL", "DR"}
_ALLOWED_STATE_DRIVER_MODEL_KINDS = {"ballistic_2d", "uniform_circular_2d", "sampled_path_2d"}


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


@lru_cache(maxsize=1)
def _load_anchor_dictionary() -> dict[str, set[str]]:
    path = Path(__file__).resolve().parents[1] / "llm_constraints" / "specs" / "anchors_dictionary.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    components = raw.get("components")
    if not isinstance(components, dict):
        return {}

    result: dict[str, set[str]] = {}
    for component_type, payload in components.items():
        if not isinstance(component_type, str) or not isinstance(payload, dict):
            continue
        anchors = payload.get("anchors")
        if not isinstance(anchors, list):
            continue
        normalized = {str(item).strip().lower() for item in anchors if str(item).strip()}
        if normalized:
            result[component_type] = normalized
    return result


def _first_nonempty_str(args: dict, *keys: str) -> str | None:
    for key in keys:
        value = args.get(key)
        if isinstance(value, str):
            candidate = value.strip()
            if candidate:
                return candidate
    return None


def _allowed_anchor_names(part_type: str, anchor_dict: dict[str, set[str]]) -> set[str]:
    return {name.lower() for name in anchor_dict.get(part_type, set())}


def _validate_anchor_name(
    *,
    object_id: str,
    constraint_index: int,
    role: str,
    part_id: str | None,
    anchor: str | None,
    part_type_by_id: dict[str, str],
    anchor_dict: dict[str, set[str]],
) -> list[ValidationErrorItem]:
    if not part_id or not anchor:
        return []

    part_type = part_type_by_id.get(part_id)
    if part_type is None:
        return []

    anchor_key = anchor.strip().lower()
    allowed = _allowed_anchor_names(part_type, anchor_dict)
    if anchor_key in allowed:
        return []

    allowed_text = ", ".join(sorted(allowed))
    return [
        ValidationErrorItem(
            f"objects.{object_id}.params.graph.constraints[{constraint_index}] "
            f"{role}='{anchor}' invalid for part '{part_id}' ({part_type}); allowed: {allowed_text}"
        )
    ]


def _autofix_objects(plan: ScenePlan) -> bool:
    changed = False
    for obj in plan.objects.values():
        if obj.type == "TextBlock":
            text = obj.params.get("text")
            if text is None:
                text = obj.params.get("content", "")
            normalized_text = str(text)
            normalized_text = shorten_inline_math_subscripts(normalized_text, max_letters=2)
            if obj.params.get("text") != normalized_text:
                obj.params["text"] = normalized_text
                changed = True
            if "content" in obj.params:
                obj.params.pop("content", None)
                changed = True
            continue

        if obj.type != "Formula":
            if obj.type == "CompositeObject":
                graph = obj.params.get("graph")
                if isinstance(graph, dict) and _autofix_ballistic_orientation_defaults_in_graph(graph):
                    changed = True
            continue

        latex = obj.params.get("latex")
        if latex is None:
            latex = obj.params.get("content", "")
        normalized_latex = str(latex).strip()
        normalized_latex = shorten_latex_subscripts(normalized_latex, max_letters=2)

        if _contains_cjk(normalized_latex):
            obj.type = "TextBlock"
            obj.params = {"text": normalized_latex}
            changed = True
            continue

        if obj.params.get("latex") != normalized_latex:
            obj.params["latex"] = normalized_latex
            changed = True
        if "content" in obj.params:
            obj.params.pop("content", None)
            changed = True

    return changed


def _autofix_ballistic_orientation_defaults_in_graph(graph: dict) -> bool:
    parts = graph.get("parts")
    motions = graph.get("motions")
    if not isinstance(parts, list) or not isinstance(motions, list):
        return False

    part_type_by_id: dict[str, str] = {}
    for part in parts:
        if not isinstance(part, dict):
            continue
        part_id = part.get("id")
        part_type = part.get("type")
        if isinstance(part_id, str) and part_id.strip() and isinstance(part_type, str) and part_type.strip():
            part_type_by_id[part_id.strip()] = part_type.strip()

    changed = False
    for motion in motions:
        if not isinstance(motion, dict):
            continue
        if str(motion.get("type", "")).strip() != "state_driver":
            continue

        args = motion.get("args")
        if not isinstance(args, dict):
            continue
        part_id_raw = args.get("part_id")
        part_id = part_id_raw.strip() if isinstance(part_id_raw, str) and part_id_raw.strip() else ""
        if not part_id:
            continue
        if part_type_by_id.get(part_id) not in _PROJECTILE_HORIZONTAL_PART_TYPES:
            continue

        model_cfg = args.get("model")
        if not isinstance(model_cfg, dict):
            continue
        model_kind = str(model_cfg.get("kind", "")).strip().lower()
        if model_kind != "ballistic_2d":
            continue

        mode_raw = args.get("orient_mode", args.get("theta_mode", args.get("orient")))
        mode = mode_raw.strip().lower() if isinstance(mode_raw, str) and mode_raw.strip() else ""
        has_theta_literal = "theta" in args or "angle" in args

        if not mode:
            args["orient_mode"] = "fixed"
            changed = True
            if not has_theta_literal:
                args["theta"] = 0.0
                changed = True
            continue

        if mode == "fixed" and not has_theta_literal:
            args["theta"] = 0.0
            changed = True

    return changed


def _validate_known_param_keys(object_id: str, obj_type: str, params: dict) -> list[ValidationErrorItem]:
    allowed = PHYSICS_OBJECT_PARAM_SPECS.get(obj_type)
    if allowed is None:
        return []
    unknown = sorted([k for k in params.keys() if k not in set(allowed)])
    if not unknown:
        return []
    return [ValidationErrorItem(f"objects.{object_id} {obj_type} has unknown params: {', '.join(unknown)}")]


def _validate_custom_object(object_id: str, params: dict) -> list[ValidationErrorItem]:
    errors: list[ValidationErrorItem] = []

    code_key = params.get("code_key")
    if not isinstance(code_key, str) or not code_key.strip():
        errors.append(ValidationErrorItem(f"objects.{object_id} CustomObject needs params.code_key (non-empty string)"))

    spec = params.get("spec")
    if spec is not None and not isinstance(spec, dict):
        errors.append(ValidationErrorItem(f"objects.{object_id} CustomObject params.spec must be an object"))

    code_file = params.get("code_file")
    if code_file is not None and (not isinstance(code_file, str) or not code_file.strip()):
        errors.append(ValidationErrorItem(f"objects.{object_id} CustomObject params.code_file must be a non-empty string"))

    motion_span_s = params.get("motion_span_s")
    if motion_span_s is not None:
        parsed = _safe_float(motion_span_s)
        if parsed is None:
            errors.append(ValidationErrorItem(f"objects.{object_id} CustomObject params.motion_span_s must be a number"))
        elif parsed <= 0.0:
            errors.append(ValidationErrorItem(f"objects.{object_id} CustomObject params.motion_span_s must be > 0"))

    return errors


def _track_space(track_type: str, data: dict) -> str:
    explicit = str(data.get("space", "")).strip().lower()
    if explicit in {"local", "world"}:
        return explicit

    if track_type in {"line", "segment"} and {"x1", "y1", "x2", "y2"}.issubset(data):
        return "world"
    if track_type == "arc" and {"cx", "cy"}.issubset(data):
        if ("start" in data or "end" in data):
            return "world"
    if track_type == "line" and {"x0", "y0", "dx", "dy"}.issubset(data):
        return "world"
    return "local"


def _has_local_endpoints(data: dict) -> bool:
    has_anchor_a = isinstance(data.get("anchor_a"), str) and bool(str(data.get("anchor_a")).strip())
    has_anchor_b = isinstance(data.get("anchor_b"), str) and bool(str(data.get("anchor_b")).strip())
    return has_anchor_a and has_anchor_b


def _has_local_arc_center(data: dict) -> bool:
    if isinstance(data.get("center"), str) and str(data.get("center")).strip():
        return True
    return (
        isinstance(data.get("cx"), (int, float))
        and not isinstance(data.get("cx"), bool)
        and isinstance(data.get("cy"), (int, float))
        and not isinstance(data.get("cy"), bool)
    )


def _to_float_or_none(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _is_numeric_coord_vector(value: object) -> bool:
    if not isinstance(value, (list, tuple)):
        return False
    if len(value) not in {2, 3}:
        return False
    return all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)


def _validate_motion_timeline(
    *,
    motion_path: str,
    timeline: list[dict],
    param_key: str,
    param_context: str,
    range_min: float | None = None,
    range_max: float | None = None,
) -> tuple[list[ValidationErrorItem], list[tuple[float, float]]]:
    errors: list[ValidationErrorItem] = []
    points: list[tuple[float, float]] = []

    if len(timeline) < 2:
        errors.append(ValidationErrorItem(f"{motion_path}.timeline must contain at least 2 keyframes"))

    prev_t: float | None = None
    for point_index, point in enumerate(timeline):
        if not isinstance(point, dict):
            errors.append(ValidationErrorItem(f"{motion_path}.timeline[{point_index}] must be an object"))
            continue

        t_value = _safe_float(point.get("t"))
        if t_value is None:
            errors.append(ValidationErrorItem(f"{motion_path}.timeline[{point_index}].t must be numeric"))
            continue
        if prev_t is not None and t_value <= prev_t:
            errors.append(
                ValidationErrorItem(
                    f"{motion_path}.timeline[{point_index}].t must be strictly increasing"
                )
            )
        prev_t = t_value

        raw_param = point.get(param_key)
        value = _safe_float(raw_param)
        if value is None:
            errors.append(
                ValidationErrorItem(
                    f"{motion_path}.timeline[{point_index}].{param_key} must be numeric for {param_context}"
                )
            )
            continue
        if range_min is not None and value < range_min:
            errors.append(
                ValidationErrorItem(
                    f"{motion_path}.timeline[{point_index}].{param_key} out of range [{range_min},{range_max}]: {value}"
                )
            )
            continue
        if range_max is not None and value > range_max:
            errors.append(
                ValidationErrorItem(
                    f"{motion_path}.timeline[{point_index}].{param_key} out of range [{range_min},{range_max}]: {value}"
                )
            )
            continue
        points.append((float(t_value), float(value)))

    return errors, points


def _validate_state_driver_model(
    *,
    motion_path: str,
    args: dict,
    timeline_points: list[tuple[float, float]],
) -> list[ValidationErrorItem]:
    errors: list[ValidationErrorItem] = []
    model = args.get("model")
    if not isinstance(model, dict):
        return [ValidationErrorItem(f"{motion_path}.args.model is required for state_driver")]

    kind_raw = model.get("kind")
    kind = str(kind_raw).strip().lower() if isinstance(kind_raw, str) else ""
    if kind not in _ALLOWED_STATE_DRIVER_MODEL_KINDS:
        allowed_text = ", ".join(sorted(_ALLOWED_STATE_DRIVER_MODEL_KINDS))
        return [ValidationErrorItem(f"{motion_path}.args.model.kind must be one of: {allowed_text}")]

    params = model.get("params")
    if not isinstance(params, dict):
        return [ValidationErrorItem(f"{motion_path}.args.model.params must be an object")]

    if kind == "ballistic_2d":
        for key in ("x0", "y0", "vx0", "vy0"):
            if _safe_float(params.get(key)) is None:
                errors.append(ValidationErrorItem(f"{motion_path}.args.model.params.{key} must be numeric"))
        g = params.get("g")
        if g is not None and _safe_float(g) is None:
            errors.append(ValidationErrorItem(f"{motion_path}.args.model.params.g must be numeric when provided"))
        return errors

    if kind == "uniform_circular_2d":
        for key in ("cx", "cy", "r", "omega"):
            if _safe_float(params.get(key)) is None:
                errors.append(ValidationErrorItem(f"{motion_path}.args.model.params.{key} must be numeric"))
        if _safe_float(params.get("r")) is not None and float(params.get("r")) <= 0.0:
            errors.append(ValidationErrorItem(f"{motion_path}.args.model.params.r must be > 0"))
        phi0 = params.get("phi0")
        if phi0 is not None and _safe_float(phi0) is None:
            errors.append(ValidationErrorItem(f"{motion_path}.args.model.params.phi0 must be numeric when provided"))
        return errors

    # sampled_path_2d
    samples = params.get("samples")
    if not isinstance(samples, list) or len(samples) < 2:
        return [ValidationErrorItem(f"{motion_path}.args.model.params.samples must be an array with >= 2 items")]

    parsed_taus: list[float] = []
    prev_tau: float | None = None
    for sample_index, sample in enumerate(samples):
        sample_path = f"{motion_path}.args.model.params.samples[{sample_index}]"
        if not isinstance(sample, dict):
            errors.append(ValidationErrorItem(f"{sample_path} must be an object"))
            continue
        tau = _safe_float(sample.get("tau"))
        x = _safe_float(sample.get("x"))
        y = _safe_float(sample.get("y"))
        if tau is None:
            errors.append(ValidationErrorItem(f"{sample_path}.tau must be numeric"))
            continue
        if x is None:
            errors.append(ValidationErrorItem(f"{sample_path}.x must be numeric"))
        if y is None:
            errors.append(ValidationErrorItem(f"{sample_path}.y must be numeric"))
        if tau < 0.0 or tau > 1.0:
            errors.append(ValidationErrorItem(f"{sample_path}.tau out of range [0,1]: {tau}"))
            continue
        if prev_tau is not None and tau <= prev_tau:
            errors.append(ValidationErrorItem(f"{sample_path}.tau must be strictly increasing"))
            continue
        prev_tau = tau
        parsed_taus.append(float(tau))

    if parsed_taus and timeline_points:
        tau_min = parsed_taus[0]
        tau_max = parsed_taus[-1]
        for point_index, (_, tau_value) in enumerate(timeline_points):
            if tau_value < tau_min - 1e-9 or tau_value > tau_max + 1e-9:
                errors.append(
                    ValidationErrorItem(
                        f"{motion_path}.timeline[{point_index}] tau {tau_value} is outside sampled range [{tau_min},{tau_max}]"
                    )
                )

    return errors


def _validate_composite_object(
    *,
    object_id: str,
    params: dict,
    allowed_object_types: set[str],
) -> list[ValidationErrorItem]:
    graph = params.get("graph")
    if graph is None:
        return [ValidationErrorItem(f"objects.{object_id} CompositeObject needs params.graph")]
    if not isinstance(graph, dict):
        return [ValidationErrorItem(f"objects.{object_id} CompositeObject params.graph must be an object")]

    try:
        model = CompositeGraph.model_validate(graph)
    except Exception as exc:  # noqa: BLE001
        return [ValidationErrorItem(f"objects.{object_id} CompositeObject invalid params.graph: {exc}")]

    errors: list[ValidationErrorItem] = []
    allowed_part_types = set(allowed_object_types) - {"CompositeObject", "CustomObject"}
    part_type_by_id = {part.id: part.type for part in model.parts}
    part_params_by_id = {part.id: dict(part.params or {}) for part in model.parts}
    track_type_by_id = {track.id: str(track.type).strip().lower() for track in model.tracks}
    anchor_dict = _load_anchor_dictionary()

    for index, part in enumerate(model.parts):
        path = f"objects.{object_id}.params.graph.parts[{index}]"
        if part.type not in allowed_part_types:
            errors.append(ValidationErrorItem(f"{path}.type not allowed: {part.type}"))
            continue
        errors.extend(_validate_known_param_keys(f"{object_id}.params.graph.parts[{index}]", part.type, part.params))
        if "center" in part.params and not _is_numeric_coord_vector(part.params.get("center")):
            errors.append(
                ValidationErrorItem(
                    f"{path}.params.center must be coordinate array [x,y] or [x,y,z] (object form is forbidden)"
                )
            )
        if part.type == "Rod" and _ARC_ID_HINT_RE.search(part.id.strip().lower()):
            errors.append(
                ValidationErrorItem(
                    f"{path}.type uses Rod for arc-like id '{part.id}'; use ArcTrack/SemicircleGroove instead"
                )
            )

    has_arc_track = any(track.type == "arc" for track in model.tracks)
    has_curved_part = any(part.type in _CURVED_PART_TYPES for part in model.parts)
    if has_arc_track and not has_curved_part:
        errors.append(
            ValidationErrorItem(
                f"objects.{object_id}.params.graph has arc track(s) but no curved part "
                f"({', '.join(sorted(_CURVED_PART_TYPES))})"
            )
        )

    for track_index, track in enumerate(model.tracks):
        track_path = f"objects.{object_id}.params.graph.tracks[{track_index}]"
        data = dict(track.data or {})
        ttype = str(track.type).strip().lower()
        if ttype == "line":
            errors.append(
                ValidationErrorItem(
                    f"{track_path}.type 'line' is disabled in current pipeline strategy; use segment or arc"
                )
            )
            continue
        if ttype not in {"segment", "arc"}:
            errors.append(ValidationErrorItem(f"{track_path}.type not supported: {ttype}"))
            continue
        if ttype == "segment":
            allowed_segment_keys = {"space", "part_id", "anchor_a", "anchor_b", "x1", "y1", "x2", "y2"}
            unknown = sorted(key for key in data.keys() if key not in allowed_segment_keys)
            if unknown:
                errors.append(
                    ValidationErrorItem(
                        f"{track_path}.data has unknown keys for segment: {', '.join(unknown)}"
                    )
                )
        if ttype == "arc":
            allowed_arc_keys = {"space", "part_id", "center", "cx", "cy", "radius", "start", "end"}
            unknown = sorted(key for key in data.keys() if key not in allowed_arc_keys)
            if unknown:
                errors.append(
                    ValidationErrorItem(
                        f"{track_path}.data has unknown keys for arc: {', '.join(unknown)}"
                    )
                )
        space = _track_space(ttype, data)

        if space == "world":
            if ttype == "segment":
                if not {"x1", "y1", "x2", "y2"}.issubset(data):
                    errors.append(ValidationErrorItem(f"{track_path}.data(world) missing segment coordinates x1/y1/x2/y2"))
                for key in ("x1", "y1", "x2", "y2"):
                    if _safe_float(data.get(key)) is None:
                        errors.append(ValidationErrorItem(f"{track_path}.data.{key} must be numeric"))
                forbidden_keys = [key for key in ("part_id", "anchor_a", "anchor_b") if key in data]
                if forbidden_keys:
                    errors.append(
                        ValidationErrorItem(
                            f"{track_path}.data(world) forbids local keys: {', '.join(forbidden_keys)}"
                        )
                    )
            if ttype == "arc":
                has_center = "cx" in data and "cy" in data
                has_angles = "start" in data and "end" in data
                has_radius = "radius" in data
                if not (has_center and has_angles and has_radius):
                    errors.append(ValidationErrorItem(f"{track_path}.data(world) missing arc coordinates"))
                for key in ("cx", "cy", "radius", "start", "end"):
                    if key in data and _safe_float(data.get(key)) is None:
                        errors.append(ValidationErrorItem(f"{track_path}.data.{key} must be numeric"))
                forbidden_keys = [key for key in ("part_id", "center") if key in data]
                if forbidden_keys:
                    errors.append(
                        ValidationErrorItem(
                            f"{track_path}.data(world) forbids local keys: {', '.join(forbidden_keys)}"
                        )
                    )
            continue

        part_id = _first_nonempty_str(data, "part_id")
        if not part_id:
            errors.append(ValidationErrorItem(f"{track_path}.data(local) requires part_id"))
            continue
        if part_id not in part_type_by_id:
            errors.append(ValidationErrorItem(f"{track_path}.data.part_id references unknown part id: {part_id}"))
            continue

        if ttype == "segment":
            if any(key in data for key in ("x1", "y1", "x2", "y2")):
                errors.append(
                    ValidationErrorItem(
                        f"{track_path}.data(local segment) forbids world coordinates x1/y1/x2/y2"
                    )
                )
            has_anchor_pair = _has_local_endpoints(data)
            if not has_anchor_pair:
                errors.append(ValidationErrorItem(f"{track_path}.data(local segment) requires anchor_a and anchor_b"))
            part_type = part_type_by_id.get(part_id, "")
            allowed = _allowed_anchor_names(part_type, anchor_dict)
            for role in ("anchor_a", "anchor_b"):
                anchor_name = _first_nonempty_str(data, role)
                if not anchor_name:
                    continue
                if anchor_name.strip().lower() in allowed:
                    continue
                allowed_text = ", ".join(sorted(allowed))
                errors.append(
                    ValidationErrorItem(
                        f"{track_path}.data.{role}='{anchor_name}' invalid for part '{part_id}' "
                        f"({part_type}); allowed: {allowed_text}"
                    )
                )
            continue

        # local arc
        if "center" in data and not isinstance(data.get("center"), str):
            errors.append(ValidationErrorItem(f"{track_path}.data.center must be anchor name string"))
        has_center = _has_local_arc_center(data)
        has_radius = "radius" in data
        has_angles = "start" in data and "end" in data
        if not has_center:
            errors.append(ValidationErrorItem(f"{track_path}.data(local arc) missing center or cx/cy"))
        if not has_radius:
            errors.append(ValidationErrorItem(f"{track_path}.data(local arc) missing radius"))
        if not has_angles:
            errors.append(ValidationErrorItem(f"{track_path}.data(local arc) missing start/end"))

        part_type = part_type_by_id.get(part_id, "")
        if "center" in data:
            center_anchor = _first_nonempty_str(data, "center")
            if center_anchor:
                allowed = _allowed_anchor_names(part_type, anchor_dict)
                if center_anchor.strip().lower() not in allowed:
                    allowed_text = ", ".join(sorted(allowed))
                    errors.append(
                        ValidationErrorItem(
                            f"{track_path}.data.center='{center_anchor}' invalid for part '{part_id}' "
                            f"({part_type}); allowed: {allowed_text}"
                        )
                    )
        if ("cx" in data) ^ ("cy" in data):
            errors.append(ValidationErrorItem(f"{track_path}.data(local arc) cx/cy must appear together"))
        for key in ("cx", "cy", "radius", "start", "end"):
            if key in data and _safe_float(data.get(key)) is None:
                errors.append(ValidationErrorItem(f"{track_path}.data.{key} must be numeric"))

        part_params = part_params_by_id.get(part_id, {})
        part_start = _to_float_or_none(part_params.get("start"))
        part_end = _to_float_or_none(part_params.get("end"))
        track_start = _to_float_or_none(data.get("start"))
        track_end = _to_float_or_none(data.get("end"))
        if part_start is not None and track_start is not None and abs(part_start - track_start) > 1e-6:
            errors.append(
                ValidationErrorItem(
                    f"{track_path}.data.start ({track_start}) must match {part_id}.params.start ({part_start})"
                )
            )
        if part_end is not None and track_end is not None and abs(part_end - track_end) > 1e-6:
            errors.append(
                ValidationErrorItem(
                    f"{track_path}.data.end ({track_end}) must match {part_id}.params.end ({part_end})"
                )
            )

    for index, constraint in enumerate(model.constraints):
        args = dict(constraint.args or {})
        for message in validate_constraint_args(constraint.type, args):
            errors.append(
                ValidationErrorItem(
                    f"objects.{object_id}.params.graph.constraints[{index}] {message}"
                )
            )

        if constraint.type == "attach":
            part_a = _first_nonempty_str(args, "part_a", "from_part_id", "source_part_id", "part_id")
            part_b = _first_nonempty_str(args, "part_b", "to_part_id", "target_part_id")
            anchor_a = _first_nonempty_str(args, "anchor_a", "from_anchor", "anchor")
            anchor_b = _first_nonempty_str(args, "anchor_b", "to_anchor")
            errors.extend(
                _validate_anchor_name(
                    object_id=object_id,
                    constraint_index=index,
                    role="anchor_a",
                    part_id=part_a,
                    anchor=anchor_a,
                    part_type_by_id=part_type_by_id,
                    anchor_dict=anchor_dict,
                )
            )
            errors.extend(
                _validate_anchor_name(
                    object_id=object_id,
                    constraint_index=index,
                    role="anchor_b",
                    part_id=part_b,
                    anchor=anchor_b,
                    part_type_by_id=part_type_by_id,
                    anchor_dict=anchor_dict,
                )
            )
        elif constraint.type == "on_track_pose":
            part_id = _first_nonempty_str(args, "part_id")
            anchor = _first_nonempty_str(args, "anchor")
            errors.extend(
                _validate_anchor_name(
                    object_id=object_id,
                    constraint_index=index,
                    role="anchor",
                    part_id=part_id,
                    anchor=anchor,
                    part_type_by_id=part_type_by_id,
                    anchor_dict=anchor_dict,
                )
            )
            track_id = _first_nonempty_str(args, "track_id")
            if track_id and track_type_by_id.get(track_id) in {"segment", "arc"}:
                s_value = _safe_float(args.get("s", args.get("t")))
                if s_value is None:
                    errors.append(
                        ValidationErrorItem(
                            f"objects.{object_id}.params.graph.constraints[{index}] "
                            "on_track_pose requires numeric s (or t) for segment/arc track"
                        )
                    )
                elif s_value < 0.0 or s_value > 1.0:
                    errors.append(
                        ValidationErrorItem(
                            f"objects.{object_id}.params.graph.constraints[{index}] "
                            f"on_track_pose s out of range [0,1] for segment/arc track: {s_value}"
                        )
                    )

    for motion_index, motion in enumerate(model.motions):
        motion_path = f"objects.{object_id}.params.graph.motions[{motion_index}]"
        motion_type = str(motion.type).strip()
        args = dict(motion.args or {})
        if motion_type == "on_track":
            part_id = _first_nonempty_str(args, "part_id")
            if not part_id:
                errors.append(ValidationErrorItem(f"{motion_path}.args.part_id is required for on_track"))
            elif part_id not in part_type_by_id:
                errors.append(ValidationErrorItem(f"{motion_path}.args.part_id references unknown part id: {part_id}"))
            track_id = _first_nonempty_str(args, "track_id")
            if not track_id:
                errors.append(ValidationErrorItem(f"{motion_path}.args.track_id is required for on_track"))
                continue
            if track_type_by_id.get(track_id) not in {"segment", "arc"}:
                errors.append(
                    ValidationErrorItem(
                        f"{motion_path}.args.track_id='{track_id}' must reference a segment/arc track"
                    )
                )
                continue
            param_key = str(args.get("param_key", "s")).strip() or "s"
            timeline_errors, _ = _validate_motion_timeline(
                motion_path=motion_path,
                timeline=list(motion.timeline or []),
                param_key=param_key,
                param_context="segment/arc on_track",
                range_min=0.0,
                range_max=1.0,
            )
            errors.extend(timeline_errors)
            continue

        if motion_type == "on_track_schedule":
            part_id = _first_nonempty_str(args, "part_id")
            if not part_id:
                errors.append(ValidationErrorItem(f"{motion_path}.args.part_id is required for on_track_schedule"))
            elif part_id not in part_type_by_id:
                errors.append(ValidationErrorItem(f"{motion_path}.args.part_id references unknown part id: {part_id}"))

            param_key = str(args.get("param_key", "u")).strip() or "u"
            timeline_errors, _ = _validate_motion_timeline(
                motion_path=motion_path,
                timeline=list(motion.timeline or []),
                param_key=param_key,
                param_context="on_track_schedule",
                range_min=0.0,
                range_max=1.0,
            )
            errors.extend(timeline_errors)

            segments = args.get("segments")
            if not isinstance(segments, list) or not segments:
                errors.append(ValidationErrorItem(f"{motion_path}.args.segments is required for on_track_schedule"))
                continue

            prev_u1: float | None = None
            for segment_index, segment in enumerate(segments):
                if not isinstance(segment, dict):
                    errors.append(ValidationErrorItem(f"{motion_path}.args.segments[{segment_index}] must be an object"))
                    continue
                segment_path = f"{motion_path}.args.segments[{segment_index}]"
                track_id = _first_nonempty_str(segment, "track_id")
                if not track_id:
                    errors.append(ValidationErrorItem(f"{segment_path}.track_id is required"))
                elif track_type_by_id.get(track_id) not in {"segment", "arc"}:
                    errors.append(
                        ValidationErrorItem(f"{segment_path}.track_id='{track_id}' must reference a segment/arc track")
                    )

                s0 = _safe_float(segment.get("s0", segment.get("from_s")))
                s1 = _safe_float(segment.get("s1", segment.get("to_s")))
                if s0 is None or s1 is None:
                    errors.append(ValidationErrorItem(f"{segment_path} requires numeric s0/s1 (or from_s/to_s)"))
                else:
                    if s0 < 0.0 or s0 > 1.0:
                        errors.append(ValidationErrorItem(f"{segment_path}.s0 out of range [0,1]: {s0}"))
                    if s1 < 0.0 or s1 > 1.0:
                        errors.append(ValidationErrorItem(f"{segment_path}.s1 out of range [0,1]: {s1}"))

                u0 = _safe_float(segment.get("u0", segment.get("from_u")))
                u1 = _safe_float(segment.get("u1", segment.get("to_u")))
                if u0 is None or u1 is None:
                    errors.append(ValidationErrorItem(f"{segment_path} requires numeric u0/u1 (or from_u/to_u)"))
                else:
                    if u1 <= u0:
                        errors.append(ValidationErrorItem(f"{segment_path} requires u1 > u0"))
                    if prev_u1 is not None and abs(u0 - prev_u1) > 1e-6:
                        errors.append(
                            ValidationErrorItem(
                                f"{segment_path}.u0 must equal previous segment.u1 for continuous schedule"
                            )
                        )
                    prev_u1 = u1
            continue

        if motion_type != "state_driver":
            errors.append(
                ValidationErrorItem(
                    f"{motion_path}.type not supported: {motion_type} (allowed: on_track, on_track_schedule, state_driver)"
                )
            )
            continue

        part_id = _first_nonempty_str(args, "part_id")
        if not part_id:
            errors.append(ValidationErrorItem(f"{motion_path}.args.part_id is required for state_driver"))
            continue
        if part_id not in part_type_by_id:
            errors.append(ValidationErrorItem(f"{motion_path}.args.part_id references unknown part id: {part_id}"))
            continue

        mode = str(args.get("mode", "")).strip().lower()
        if mode != "model":
            errors.append(ValidationErrorItem(f"{motion_path}.args.mode must be 'model' for state_driver"))
            continue

        param_key = str(args.get("param_key", "tau")).strip() or "tau"
        timeline_errors, timeline_points = _validate_motion_timeline(
            motion_path=motion_path,
            timeline=list(motion.timeline or []),
            param_key=param_key,
            param_context="state_driver",
        )
        errors.extend(timeline_errors)

        if param_key != "tau":
            errors.append(ValidationErrorItem(f"{motion_path}.args.param_key must be 'tau' for state_driver"))

        errors.extend(
            _validate_state_driver_model(
                motion_path=motion_path,
                args=args,
                timeline_points=timeline_points,
            )
        )
    return errors


def _collect_scene_object_ids(plan: ScenePlan, scene_index: int) -> set[str]:
    scene = plan.scenes[scene_index]
    ids: set[str] = set(scene.layout.slots.values())
    ids.update(scene.layout.placements.keys())
    for action in scene.actions:
        if isinstance(action, PlayAction):
            ids.update(action.targets)
            if action.src:
                ids.add(action.src)
            if action.dst:
                ids.add(action.dst)
    ids.update(scene.keep)
    return {x for x in ids if x}


def _choose_template_type(object_count: int) -> str:
    if object_count <= 2:
        return "hero_side"
    if object_count <= 4:
        return "grid_2x2"
    if object_count <= 6:
        return "left3_right3"
    if object_count <= 8:
        return "left4_right4"
    return "grid_3x3"


def _count_formula_objects(plan: ScenePlan, object_ids: set[str]) -> int:
    return sum(1 for oid in object_ids if oid in plan.objects and plan.objects[oid].type == "Formula")


def _count_text_overflow(plan: ScenePlan, object_ids: set[str], *, max_chars: int) -> list[str]:
    overflow_ids: list[str] = []
    for oid in object_ids:
        obj = plan.objects.get(oid)
        if obj is None or obj.type != "TextBlock":
            continue
        text = obj.params.get("text")
        if text is None:
            text = obj.params.get("content", "")
        if len(str(text)) > max_chars:
            overflow_ids.append(oid)
    return overflow_ids


def _safe_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _validate_free_layout_field(
    *,
    scene_index: int,
    object_id: str,
    field_name: str,
    value: object,
    low: float,
    high: float,
    include_low: bool,
) -> ValidationErrorItem | None:
    parsed = _safe_float(value)
    if parsed is None:
        return ValidationErrorItem(
            f"scenes[{scene_index}].layout.placements[{object_id}].{field_name} must be a number"
        )
    if include_low:
        if parsed < low or parsed > high:
            return ValidationErrorItem(
                f"scenes[{scene_index}].layout.placements[{object_id}].{field_name} out of range [{low},{high}]"
            )
    else:
        if parsed <= low or parsed > high:
            return ValidationErrorItem(
                f"scenes[{scene_index}].layout.placements[{object_id}].{field_name} out of range ({low},{high}]"
            )
    return None


def _motion_timeline_span(motion: object) -> float:
    if not isinstance(motion, dict):
        return 0.0
    timeline = motion.get("timeline")
    if not isinstance(timeline, list):
        return 0.0
    times: list[float] = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        t_val = _safe_float(item.get("t"))
        if t_val is None:
            continue
        times.append(t_val)
    if len(times) < 2:
        return 0.0
    return max(times) - min(times)


def _composite_motion_span(params: dict) -> float:
    graph = params.get("graph")
    if not isinstance(graph, dict):
        return 0.0
    motions = graph.get("motions")
    if not isinstance(motions, list):
        return 0.0
    max_span = 0.0
    for motion in motions:
        span = _motion_timeline_span(motion)
        if span > max_span:
            max_span = span
    return max_span


def _custom_object_motion_span(params: dict) -> float:
    value = _safe_float(params.get("motion_span_s"))
    if value is None or value <= 0.0:
        return 0.0
    return value


def _scene_motion_span(plan: ScenePlan, object_ids: set[str]) -> float:
    max_span = 0.0
    for object_id in object_ids:
        obj = plan.objects.get(object_id)
        if obj is None:
            continue
        span = 0.0
        if obj.type == "CompositeObject":
            span = _composite_motion_span(obj.params)
        elif obj.type == "CustomObject":
            span = _custom_object_motion_span(obj.params)
        if span > max_span:
            max_span = span
    return max_span


def autofix_plan(plan: ScenePlan) -> bool:
    """
    尽力而为的自动修复，使 LLM 输出可执行。

    MVP 中该策略刻意保持保守：
    - 当 template 缺失/未知时，自动选择一个合法模板
    - 使用 `template.slot_order` 将对象重新分配到合法 slots
    - 删除无效 slots / 去重重复对象
    """

    changed = False

    if _autofix_objects(plan):
        changed = True

    for scene_index, scene in enumerate(plan.scenes):
        object_ids = sorted(
            _collect_scene_object_ids(plan, scene_index),
            key=lambda oid: (plan.objects.get(oid).priority if oid in plan.objects else 999, oid),
        )
        if not object_ids:
            continue

        if scene.layout.type == "free":
            if scene.layout.slots:
                scene.layout.slots = {}
                changed = True
            if scene.layout.params:
                scene.layout.params = {}
                changed = True
            cleaned_placements = {k: v for k, v in scene.layout.placements.items() if k in plan.objects}
            if cleaned_placements != scene.layout.placements:
                scene.layout.placements = cleaned_placements
                changed = True
            continue

        if scene.layout.params:
            cleaned_params = sanitize_params(scene.layout.type, scene.layout.params)
            if cleaned_params != scene.layout.params:
                scene.layout.params = cleaned_params
                changed = True

        template = TEMPLATE_REGISTRY.get(scene.layout.type)
        if template is None:
            scene.layout.type = _choose_template_type(len(object_ids))
            template = TEMPLATE_REGISTRY[scene.layout.type]
            changed = True

        # 删除无效的插槽键
        cleaned_slots = {k: v for k, v in scene.layout.slots.items() if k in template.slots and v in plan.objects}
        if cleaned_slots != scene.layout.slots:
            scene.layout.slots = cleaned_slots
            changed = True

        # 去重对象 id（保留首次出现的位置）
        used: set[str] = set()
        deduped: dict[str, str] = {}
        for slot_id in template.slot_order:
            if slot_id not in scene.layout.slots:
                continue
            oid = scene.layout.slots[slot_id]
            if oid in used:
                changed = True
                continue
            used.add(oid)
            deduped[slot_id] = oid
        if deduped != scene.layout.slots:
            scene.layout.slots = deduped
            changed = True

        # 按优先级把剩余对象填入空插槽
        remaining = [oid for oid in object_ids if oid not in used]
        free_slots = [s for s in template.slot_order if s not in scene.layout.slots]
        if remaining and not free_slots:
            continue

        for slot_id, oid in zip(free_slots, remaining, strict=False):
            scene.layout.slots[slot_id] = oid
            changed = True

    return changed


def validate_plan(plan: ScenePlan) -> list[ValidationErrorItem]:
    enums = load_enums()
    app = load_app_config()

    errors: list[ValidationErrorItem] = []
    pedagogy = plan.pedagogy_plan
    budget = pedagogy.cognitive_budget if pedagogy is not None else None
    has_check_scene = False
    allowed_roles = {"diagram", "title", "core_eq", "support_eq", "conclusion", "check", "hint"}

    for object_id, obj in plan.objects.items():
        if obj.type not in enums["object_types"]:
            errors.append(ValidationErrorItem(f"objects.{object_id}.type not allowed: {obj.type}"))
        else:
            errors.extend(_validate_known_param_keys(object_id, obj.type, obj.params))

        if obj.type == "CompositeObject":
            errors.extend(
                _validate_composite_object(
                    object_id=object_id,
                    params=obj.params,
                    allowed_object_types=enums["object_types"],
                )
            )
        if obj.type == "CustomObject":
            errors.extend(_validate_custom_object(object_id, obj.params))

        if obj.type == "TextBlock":
            text = obj.params.get("text")
            content = obj.params.get("content")
            if text is None and content is None:
                errors.append(ValidationErrorItem(f"objects.{object_id} TextBlock needs params.text"))
            else:
                normalized_text = str(text if text is not None else content)
                if has_unbalanced_inline_math_delimiters(normalized_text):
                    errors.append(
                        ValidationErrorItem(f"objects.{object_id} TextBlock has unbalanced $...$ delimiters")
                    )
                if has_latex_tokens_outside_inline_math(normalized_text):
                    errors.append(
                        ValidationErrorItem(f"objects.{object_id} TextBlock has LaTeX tokens outside $...$")
                    )

        if obj.type == "Formula":
            latex = obj.params.get("latex")
            if latex is None:
                errors.append(ValidationErrorItem(f"objects.{object_id} Formula needs params.latex"))
            else:
                latex_text = str(latex).strip()
                if not latex_text:
                    errors.append(ValidationErrorItem(f"objects.{object_id} Formula params.latex cannot be empty"))
                if _contains_cjk(latex_text):
                    errors.append(
                        ValidationErrorItem(
                            f"objects.{object_id} Formula params.latex contains CJK characters; use TextBlock instead"
                        )
                    )

        size_level = obj.style.get("size_level") if isinstance(obj.style, dict) else None
        if size_level is not None and str(size_level).upper() not in {"S", "M", "L", "XL"}:
            errors.append(ValidationErrorItem(f"objects.{object_id}.style.size_level must be S/M/L/XL"))

    for scene_index, scene in enumerate(plan.scenes):
        if scene.layout.type not in enums["layout_types"]:
            errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.type not allowed: {scene.layout.type}"))

        if scene.layout.type == "free":
            if scene.layout.slots:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.slots must be empty for free layout"))
            if scene.layout.params:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.params must be empty for free layout"))
            if not scene.layout.placements:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.placements must not be empty"))
            if len(scene.layout.placements) > 9:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}] uses more than 9 objects in placements"))

            for object_id, placement in scene.layout.placements.items():
                if object_id not in plan.objects:
                    errors.append(
                        ValidationErrorItem(
                            f"scenes[{scene_index}].layout.placements[{object_id}] unknown object id: {object_id}"
                        )
                    )
                    continue
                for field_name, low, high, include_low in (
                    ("cx", 0.0, 1.0, True),
                    ("cy", 0.0, 1.0, True),
                    ("w", 0.0, 1.0, False),
                    ("h", 0.0, 1.0, False),
                ):
                    err = _validate_free_layout_field(
                        scene_index=scene_index,
                        object_id=object_id,
                        field_name=field_name,
                        value=getattr(placement, field_name),
                        low=low,
                        high=high,
                        include_low=include_low,
                    )
                    if err is not None:
                        errors.append(err)
                anchor = str(placement.anchor).strip().upper()
                if anchor not in _ALLOWED_LAYOUT_ANCHORS:
                    errors.append(
                        ValidationErrorItem(
                            f"scenes[{scene_index}].layout.placements[{object_id}].anchor invalid: {placement.anchor}"
                        )
                    )
        else:
            template = TEMPLATE_REGISTRY.get(scene.layout.type)
            if not template:
                errors.append(ValidationErrorItem(f"Unknown layout template: {scene.layout.type}"))
                continue

            if len(set(scene.layout.slots.values())) > 9:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}] uses more than 9 objects"))

            for slot_id, object_id in scene.layout.slots.items():
                if slot_id not in template.slots:
                    errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.slots has invalid slot: {slot_id}"))
                if object_id not in plan.objects:
                    errors.append(
                        ValidationErrorItem(
                            f"scenes[{scene_index}].layout.slots.{slot_id} unknown object id: {object_id}"
                        )
                    )

            if scene.layout.params and not isinstance(scene.layout.params, dict):
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.params must be an object"))
            else:
                cleaned = sanitize_params(scene.layout.type, scene.layout.params)
                if scene.layout.params and cleaned != scene.layout.params:
                    errors.append(ValidationErrorItem(f"scenes[{scene_index}].layout.params invalid for template type"))

        referenced_ids = _collect_scene_object_ids(plan, scene_index)
        unknown = sorted([x for x in referenced_ids if x not in plan.objects])
        for object_id in unknown:
            errors.append(ValidationErrorItem(f"scenes[{scene_index}] references unknown object id: {object_id}"))
        scene_motion_span_sec = _scene_motion_span(plan, referenced_ids)

        if budget is not None and len(referenced_ids) > budget.max_visible_objects:
            errors.append(
                ValidationErrorItem(
                    f"scenes[{scene_index}] references {len(referenced_ids)} objects, exceeds pedagogy budget max_visible_objects={budget.max_visible_objects}"
                )
            )

        formula_count = _count_formula_objects(plan, referenced_ids)
        if budget is not None and formula_count > budget.max_new_formula:
            errors.append(
                ValidationErrorItem(
                    f"scenes[{scene_index}] has {formula_count} Formula objects, exceeds pedagogy budget max_new_formula={budget.max_new_formula}"
                )
            )

        if budget is not None and len(scene.new_symbols) > budget.max_new_symbols:
            errors.append(
                ValidationErrorItem(
                    f"scenes[{scene_index}].new_symbols has {len(scene.new_symbols)} items, exceeds pedagogy budget max_new_symbols={budget.max_new_symbols}"
                )
            )

        if budget is not None:
            overflow_text_ids = _count_text_overflow(plan, referenced_ids, max_chars=budget.max_text_chars)
            for object_id in overflow_text_ids:
                errors.append(
                    ValidationErrorItem(
                        f"scenes[{scene_index}] TextBlock {object_id} length exceeds pedagogy budget max_text_chars={budget.max_text_chars}"
                    )
                )

        if pedagogy is not None and pedagogy.need_single_goal and not (scene.goal or "").strip():
            errors.append(ValidationErrorItem(f"scenes[{scene_index}].goal required when pedagogy_plan.need_single_goal=true"))

        if scene.is_check_scene:
            has_check_scene = True
            if "check" not in {m.strip().lower() for m in scene.modules}:
                errors.append(
                    ValidationErrorItem(f"scenes[{scene_index}] is_check_scene=true but modules does not include 'check'")
                )
            if not (scene.goal or "").strip():
                errors.append(ValidationErrorItem(f"scenes[{scene_index}] is_check_scene=true but goal is empty"))
            if pedagogy is not None and not pedagogy.check_types:
                errors.append(
                    ValidationErrorItem(
                        f"scenes[{scene_index}] is_check_scene=true but pedagogy_plan.check_types is empty"
                    )
                )

        for object_id, role in scene.roles.items():
            if object_id not in referenced_ids:
                errors.append(
                    ValidationErrorItem(f"scenes[{scene_index}].roles references object not used in scene: {object_id}")
                )
            if str(role).strip().lower() not in allowed_roles:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].roles[{object_id}] has unknown role: {role}"))

        scene_action_duration = 0.0
        for action_index, action in enumerate(scene.actions):
            if action.op not in enums["action_ops"]:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}].op not allowed"))
            if isinstance(action, PlayAction) and action.anim not in enums["anims"]:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}].anim not allowed"))

            if isinstance(action, WaitAction):
                scene_action_duration += float(action.duration)
            elif isinstance(action, PlayAction):
                if scene_motion_span_sec > 0 and action.duration is None:
                    errors.append(
                        ValidationErrorItem(
                            f"scenes[{scene_index}].actions[{action_index}].duration required when scene has graph.motions"
                        )
                    )
                scene_action_duration += float(action.duration or app.defaults.action_duration)

            if isinstance(action, PlayAction) and action.anim == "transform":
                src = action.src or (action.targets[0] if len(action.targets) >= 1 else None)
                dst = action.dst or (action.targets[1] if len(action.targets) >= 2 else None)
                if not src or not dst:
                    errors.append(
                        ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}] transform needs src+dst")
                    )

        if scene_motion_span_sec > 0 and scene_action_duration + 1e-6 < scene_motion_span_sec:
            errors.append(
                ValidationErrorItem(
                    f"scenes[{scene_index}] action duration {scene_action_duration:.3f}s is shorter than motion span {scene_motion_span_sec:.3f}s"
                )
            )

    if pedagogy is not None and pedagogy.need_check_scene and not has_check_scene:
        errors.append(ValidationErrorItem("pedagogy_plan.need_check_scene=true but no scene has is_check_scene=true"))

    if app.slot_padding < 0 or app.slot_padding > 0.2:
        errors.append(ValidationErrorItem("configs/app.yaml render.slot_padding should be within 0..0.2"))

    return errors


def _format_errors(errors: list[ValidationErrorItem]) -> str:
    return "\n".join(f"- {e.message}" for e in errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a scene_plan.json")
    parser.add_argument("plan", nargs="?", default="cases/demo_001/scene_plan.json", help="Path to scene_plan.json")
    parser.add_argument("--autofix", action="store_true", help="Apply conservative autofix to the loaded plan")
    parser.add_argument("--write", action="store_true", help="Write the (auto)fixed plan back to the same path")
    args = parser.parse_args(argv)

    plan_path = Path(args.plan)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Plan file not found: {plan_path}", file=sys.stderr)
        return 2

    try:
        plan = ScenePlan.model_validate(raw)
    except Exception as e:  # noqa: BLE001
        print("Schema validation failed:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 2

    if args.autofix:
        changed = autofix_plan(plan)
        if changed and args.write:
            plan_path.write_text(json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    errors = validate_plan(plan)
    if errors:
        print("Plan validation failed:", file=sys.stderr)
        print(_format_errors(errors), file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
