from __future__ import annotations

from typing import Any


def _arg(args: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in args:
            return args[key]
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def _to_float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


__all__ = [
    "_arg",
    "_to_bool",
    "_to_float",
    "_to_float_or_none",
]
