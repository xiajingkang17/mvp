from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from manim import Mobject, ORIGIN

from components.base import Component, ComponentDefaults
from schema.scene_plan_models import ObjectSpec


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_PATH = ROOT_DIR / "cases" / "demo_001" / "scene_plan.json"
_MODULE_CACHE: dict[Path, tuple[int, ModuleType]] = {}
_IDENTIFIER_RE = re.compile(r"[^0-9a-zA-Z_]+")


BuilderFn = Callable[[dict[str, Any]], Mobject]
UpdaterFn = Callable[[Mobject, float, dict[str, Any]], None]


def _safe_identifier(name: str) -> str:
    return _IDENTIFIER_RE.sub("_", str(name).strip()).strip("_")


def _resolve_plan_path() -> Path:
    raw = os.environ.get("SCENE_PLAN", "").strip()
    if not raw:
        return DEFAULT_PLAN_PATH
    plan_path = Path(raw)
    if not plan_path.is_absolute():
        plan_path = (ROOT_DIR / plan_path).resolve()
    return plan_path


def _resolve_codegen_path(params: dict[str, Any]) -> Path:
    plan_dir = _resolve_plan_path().parent
    override = params.get("code_file")
    if isinstance(override, str) and override.strip():
        path = Path(override.strip())
        if not path.is_absolute():
            # Relative override is resolved against case directory first.
            by_case = (plan_dir / path).resolve()
            if by_case.exists():
                return by_case
            path = (ROOT_DIR / path).resolve()
        return path
    return plan_dir / "llm_codegen.py"


def _load_codegen_module(path: Path) -> ModuleType:
    resolved = path.resolve()
    stat = resolved.stat()
    cached = _MODULE_CACHE.get(resolved)
    if cached is not None and cached[0] == int(stat.st_mtime_ns):
        return cached[1]

    module_name = f"_llm_codegen_{abs(hash(str(resolved)))}_{int(stat.st_mtime_ns)}"
    spec = importlib.util.spec_from_file_location(module_name, str(resolved))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec from: {resolved}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE_CACHE[resolved] = (int(stat.st_mtime_ns), module)
    return module


def _resolve_builder(module: ModuleType, code_key: str) -> BuilderFn:
    builders = getattr(module, "BUILDERS", None)
    if isinstance(builders, dict):
        candidate = builders.get(code_key)
        if callable(candidate):
            return candidate

    fallback_name = _safe_identifier(code_key)
    if fallback_name:
        candidate = getattr(module, f"build_{fallback_name}", None)
        if callable(candidate):
            return candidate

    raise KeyError(
        f"Missing CustomObject builder for code_key='{code_key}'. "
        "Expected BUILDERS[code_key] or function build_<code_key>."
    )


def _resolve_updater(module: ModuleType, code_key: str) -> UpdaterFn | None:
    updaters = getattr(module, "UPDATERS", None)
    if isinstance(updaters, dict):
        candidate = updaters.get(code_key)
        if callable(candidate):
            return candidate

    fallback_name = _safe_identifier(code_key)
    if fallback_name:
        candidate = getattr(module, f"update_{fallback_name}", None)
        if callable(candidate):
            return candidate
    return None


class CustomObjectComponent(Component):
    type_name = "CustomObject"

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        _ = defaults
        params = dict(spec.params or {})
        code_key = str(params.get("code_key", "")).strip()
        if not code_key:
            raise ValueError("CustomObject requires params.code_key")

        custom_spec = params.get("spec")
        if custom_spec is None:
            custom_spec = {}
        if not isinstance(custom_spec, dict):
            raise ValueError("CustomObject params.spec must be an object when provided")

        code_path = _resolve_codegen_path(params)
        if not code_path.exists():
            raise FileNotFoundError(
                f"CustomObject code file not found: {code_path} "
                "(expected llm_codegen.py in case directory)"
            )

        module = _load_codegen_module(code_path)
        builder = _resolve_builder(module, code_key)
        updater = _resolve_updater(module, code_key)

        mobj = builder(custom_spec)
        if not isinstance(mobj, Mobject):
            raise TypeError(f"CustomObject builder '{code_key}' must return a Manim Mobject")

        base_mobj = mobj.copy()
        runtime = {"time": 0.0, "scale": 1.0, "tx": 0.0, "ty": 0.0}

        def _render_at(time_value: float) -> None:
            runtime["time"] = float(time_value)
            mobj.become(base_mobj.copy())
            if updater is not None:
                updater(mobj, float(runtime["time"]), custom_spec)
            if runtime["scale"] != 1.0:
                mobj.scale(float(runtime["scale"]), about_point=ORIGIN)
            if runtime["tx"] != 0.0 or runtime["ty"] != 0.0:
                mobj.shift([float(runtime["tx"]), float(runtime["ty"]), 0.0])

        def _set_placement(scale: float, tx: float, ty: float) -> None:
            scale_value = float(scale)
            runtime["scale"] *= scale_value
            runtime["tx"] = runtime["tx"] * scale_value + float(tx)
            runtime["ty"] = runtime["ty"] * scale_value + float(ty)
            _render_at(runtime["time"])

        def _set_placement_absolute(scale: float, tx: float, ty: float) -> None:
            runtime["scale"] = float(scale)
            runtime["tx"] = float(tx)
            runtime["ty"] = float(ty)
            _render_at(runtime["time"])

        mobj.composite_set_time = _render_at  # type: ignore[attr-defined]
        mobj.composite_set_placement = _set_placement  # type: ignore[attr-defined]
        mobj.composite_set_placement_absolute = _set_placement_absolute  # type: ignore[attr-defined]
        mobj.custom_code_key = code_key  # type: ignore[attr-defined]
        mobj.custom_code_path = str(code_path)  # type: ignore[attr-defined]

        _render_at(0.0)
        return mobj
