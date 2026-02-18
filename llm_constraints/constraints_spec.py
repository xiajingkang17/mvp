from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schema.composite_graph_models import GraphConstraint

_SPEC_PATH = Path(__file__).with_name("specs").joinpath("constraints_whitelist.json")


def _load_specs() -> dict[str, Any]:
    data = json.loads(_SPEC_PATH.read_text(encoding="utf-8"))
    constraints = data.get("constraints")
    if not isinstance(constraints, dict):
        raise ValueError("constraints_whitelist.json missing top-level 'constraints' object")
    return constraints


CONSTRAINT_SPECS: dict[str, Any] = _load_specs()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _value_type_ok(value: Any, value_type: str) -> bool:
    if value_type == "number":
        return _is_number(value)
    if value_type == "bool":
        return isinstance(value, bool)
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "point2d":
        return (
            isinstance(value, (list, tuple))
            and len(value) >= 2
            and _is_number(value[0])
            and _is_number(value[1])
        )
    return True


def _enum_contains(enum_values: list[Any], value: Any) -> bool:
    if not isinstance(value, str):
        return value in enum_values
    return value.strip().lower() in {str(item).strip().lower() for item in enum_values}


def validate_constraint_args(constraint_type: str, args: dict[str, Any]) -> list[str]:
    spec = CONSTRAINT_SPECS.get(constraint_type)
    if not isinstance(spec, dict):
        return [f"unsupported constraint type: {constraint_type}"]

    arg_specs = spec.get("args")
    if not isinstance(arg_specs, dict):
        arg_specs = spec.get("params", {})
    required_any_of = spec.get("required_any_of", [])
    errors: list[str] = []

    allowed_keys = set(arg_specs.keys())
    unknown_keys = sorted(key for key in args if key not in allowed_keys)
    if unknown_keys:
        errors.append(f"unknown args for {constraint_type}: {', '.join(unknown_keys)}")

    for aliases in required_any_of:
        if isinstance(aliases, list) and not any(alias in args for alias in aliases):
            errors.append(f"{constraint_type} requires one of: {', '.join(aliases)}")

    for name, rule in arg_specs.items():
        if name not in args:
            continue
        value = args[name]
        if not isinstance(rule, dict):
            continue
        value_type = str(rule.get("type", "")).strip()
        if value_type and not _value_type_ok(value, value_type):
            errors.append(f"{constraint_type}.{name} must be {value_type}")
            continue
        enum_values = rule.get("enum")
        if isinstance(enum_values, list) and enum_values and not _enum_contains(enum_values, value):
            errors.append(
                f"{constraint_type}.{name} must be one of: {', '.join(str(item) for item in enum_values)}"
            )
        if value_type == "number":
            number_value = float(value)
            min_value = rule.get("min")
            max_value = rule.get("max")
            if isinstance(min_value, (int, float)) and number_value < float(min_value):
                errors.append(f"{constraint_type}.{name} must be >= {float(min_value)}")
            if isinstance(max_value, (int, float)) and number_value > float(max_value):
                errors.append(f"{constraint_type}.{name} must be <= {float(max_value)}")

    if constraint_type == "midpoint":
        has_p1 = "point_1" in args or "part_1" in args or ("x1" in args and "y1" in args)
        has_p2 = "point_2" in args or "part_2" in args or ("x2" in args and "y2" in args)
        if not has_p1:
            errors.append("midpoint requires point_1 source (point_1 or part_1 or x1/y1)")
        if not has_p2:
            errors.append("midpoint requires point_2 source (point_2 or part_2 or x2/y2)")

    return errors


def validate_constraint(constraint: GraphConstraint | dict[str, Any]) -> list[str]:
    if isinstance(constraint, GraphConstraint):
        ctype = constraint.type
        args = dict(constraint.args or {})
    else:
        ctype = str(constraint.get("type", ""))
        args = dict(constraint.get("args") or {})
    return validate_constraint_args(ctype, args)
