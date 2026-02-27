from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


_DSL_ALLOWED_KINDS = {"custom", "new_component", "special_motion", "complex_effect", "hybrid"}
_STATE_DRIVER_MODEL_KINDS = {"ballistic_2d", "uniform_circular_2d", "sampled_path_2d"}


def _to_float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


class CodegenDslSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dsl_version: str = Field(default="1.0", min_length=1)
    kind: str = Field(default="custom", min_length=1)
    geometry: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    motion: dict[str, Any] = Field(default_factory=dict)
    effects: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_spec(cls, value: Any) -> Any:
        # Backward compatibility: legacy spec was a free-form object.
        # If it is not already DSL-shaped, wrap it into geometry.
        if not isinstance(value, dict):
            return value
        dsl_keys = {"dsl_version", "kind", "geometry", "style", "motion", "effects", "meta"}
        if any(k in value for k in dsl_keys):
            return value
        return {
            "dsl_version": "1.0",
            "kind": "custom",
            "geometry": dict(value),
            "style": {},
            "motion": {},
            "effects": {},
            "meta": {"legacy_wrapped": True},
        }

    @model_validator(mode="after")
    def _validate_dsl(self) -> "CodegenDslSpec":
        normalized_kind = self.kind.strip().lower()
        if normalized_kind not in _DSL_ALLOWED_KINDS:
            allowed = ", ".join(sorted(_DSL_ALLOWED_KINDS))
            raise ValueError(f"spec.kind must be one of: {allowed}")
        self.kind = normalized_kind

        motion_cfg = self.motion
        if not isinstance(motion_cfg, dict):
            raise ValueError("spec.motion must be an object")

        driver = motion_cfg.get("driver")
        if driver is None:
            return self
        if not isinstance(driver, dict):
            raise ValueError("spec.motion.driver must be an object when provided")

        required = ("target_object_id", "motion_id", "part_id", "args", "timeline")
        missing = [key for key in required if key not in driver]
        if missing:
            raise ValueError(f"spec.motion.driver missing required keys: {', '.join(missing)}")

        driver_type = str(driver.get("type", "state_driver")).strip().lower()
        if driver_type != "state_driver":
            raise ValueError("spec.motion.driver.type must be 'state_driver'")

        for key in ("target_object_id", "motion_id", "part_id"):
            value = driver.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"spec.motion.driver.{key} must be a non-empty string")

        args = driver.get("args")
        if not isinstance(args, dict):
            raise ValueError("spec.motion.driver.args must be an object")
        mode = str(args.get("mode", "")).strip().lower()
        if mode != "model":
            raise ValueError("spec.motion.driver.args.mode must be 'model'")
        param_key = str(args.get("param_key", "")).strip()
        if param_key != "tau":
            raise ValueError("spec.motion.driver.args.param_key must be 'tau'")

        model = args.get("model")
        if not isinstance(model, dict):
            raise ValueError("spec.motion.driver.args.model must be an object")
        kind = str(model.get("kind", "")).strip().lower()
        if kind not in _STATE_DRIVER_MODEL_KINDS:
            allowed = ", ".join(sorted(_STATE_DRIVER_MODEL_KINDS))
            raise ValueError(f"spec.motion.driver.args.model.kind must be one of: {allowed}")
        params = model.get("params")
        if not isinstance(params, dict):
            raise ValueError("spec.motion.driver.args.model.params must be an object")

        timeline = driver.get("timeline")
        if not isinstance(timeline, list) or len(timeline) < 2:
            raise ValueError("spec.motion.driver.timeline must contain at least 2 keyframes")
        prev_t: float | None = None
        timeline_taus: list[float] = []
        for index, point in enumerate(timeline):
            if not isinstance(point, dict):
                raise ValueError(f"spec.motion.driver.timeline[{index}] must be an object")
            t_value = _to_float_or_none(point.get("t"))
            tau_value = _to_float_or_none(point.get("tau"))
            if t_value is None:
                raise ValueError(f"spec.motion.driver.timeline[{index}].t must be numeric")
            if tau_value is None:
                raise ValueError(f"spec.motion.driver.timeline[{index}].tau must be numeric")
            if prev_t is not None and t_value <= prev_t:
                raise ValueError("spec.motion.driver.timeline t must be strictly increasing")
            prev_t = t_value
            timeline_taus.append(float(tau_value))

        if kind == "ballistic_2d":
            for key in ("x0", "y0", "vx0", "vy0"):
                if _to_float_or_none(params.get(key)) is None:
                    raise ValueError(f"ballistic_2d requires numeric params.{key}")
        elif kind == "uniform_circular_2d":
            for key in ("cx", "cy", "r", "omega"):
                if _to_float_or_none(params.get(key)) is None:
                    raise ValueError(f"uniform_circular_2d requires numeric params.{key}")
            radius = _to_float_or_none(params.get("r"))
            if radius is not None and radius <= 0.0:
                raise ValueError("uniform_circular_2d params.r must be > 0")
        else:
            samples = params.get("samples")
            if not isinstance(samples, list) or len(samples) < 2:
                raise ValueError("sampled_path_2d requires params.samples with at least 2 points")
            prev_tau: float | None = None
            sample_taus: list[float] = []
            for index, sample in enumerate(samples):
                if not isinstance(sample, dict):
                    raise ValueError(f"sampled_path_2d samples[{index}] must be an object")
                tau = _to_float_or_none(sample.get("tau"))
                x = _to_float_or_none(sample.get("x"))
                y = _to_float_or_none(sample.get("y"))
                if tau is None or x is None or y is None:
                    raise ValueError(f"sampled_path_2d samples[{index}] requires numeric tau/x/y")
                if tau < 0.0 or tau > 1.0:
                    raise ValueError(f"sampled_path_2d samples[{index}].tau must be in [0,1]")
                if prev_tau is not None and tau <= prev_tau:
                    raise ValueError("sampled_path_2d samples tau must be strictly increasing")
                prev_tau = tau
                sample_taus.append(float(tau))

            if sample_taus:
                sample_min = sample_taus[0]
                sample_max = sample_taus[-1]
                for tau in timeline_taus:
                    if tau < sample_min - 1e-9 or tau > sample_max + 1e-9:
                        raise ValueError("state_driver timeline tau is outside sampled_path_2d range")

        return self


class CodegenObjectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(min_length=1)
    code_key: str = Field(min_length=1)
    spec: CodegenDslSpec
    motion_span_s: float | None = Field(default=None, gt=0)
    notes: str | None = None


class SceneCodegenPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1", min_length=1)
    objects: list[CodegenObjectSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_unique_object_ids(self) -> "SceneCodegenPlan":
        seen: set[str] = set()
        for item in self.objects:
            object_id = item.object_id.strip()
            if object_id in seen:
                raise ValueError(f"duplicate codegen object_id: {object_id}")
            seen.add(object_id)
        return self
