from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from layout.params import sanitize_params
from layout.templates import TEMPLATE_REGISTRY
from schema.composite_graph_models import CompositeGraph
from schema.scene_plan_models import PlayAction, ScenePlan

from components.common.inline_math import (
    has_latex_tokens_outside_inline_math,
    has_unbalanced_inline_math_delimiters,
)
from components.physics.specs import PHYSICS_OBJECT_PARAM_SPECS
from .config import load_app_config, load_enums


@dataclass(frozen=True)
class ValidationErrorItem:
    message: str


_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _autofix_objects(plan: ScenePlan) -> bool:
    changed = False
    for obj in plan.objects.values():
        if obj.type == "TextBlock":
            text = obj.params.get("text")
            if text is None:
                text = obj.params.get("content", "")
            normalized_text = str(text)
            if obj.params.get("text") != normalized_text:
                obj.params["text"] = normalized_text
                changed = True
            if "content" in obj.params:
                obj.params.pop("content", None)
                changed = True
            continue

        if obj.type != "Formula":
            continue

        latex = obj.params.get("latex")
        if latex is None:
            latex = obj.params.get("content", "")
        normalized_latex = str(latex).strip()

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


def _validate_known_param_keys(object_id: str, obj_type: str, params: dict) -> list[ValidationErrorItem]:
    allowed = PHYSICS_OBJECT_PARAM_SPECS.get(obj_type)
    if allowed is None:
        return []
    unknown = sorted([k for k in params.keys() if k not in set(allowed)])
    if not unknown:
        return []
    return [ValidationErrorItem(f"objects.{object_id} {obj_type} has unknown params: {', '.join(unknown)}")]


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
    allowed_part_types = set(allowed_object_types) - {"CompositeObject"}

    for index, part in enumerate(model.parts):
        path = f"objects.{object_id}.params.graph.parts[{index}]"
        if part.type not in allowed_part_types:
            errors.append(ValidationErrorItem(f"{path}.type not allowed: {part.type}"))
            continue
        errors.extend(_validate_known_param_keys(f"{object_id}.params.graph.parts[{index}]", part.type, part.params))

    return errors


def _collect_scene_object_ids(plan: ScenePlan, scene_index: int) -> set[str]:
    scene = plan.scenes[scene_index]
    ids: set[str] = set(scene.layout.slots.values())
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
        if scene.layout.params:
            cleaned_params = sanitize_params(scene.layout.type, scene.layout.params)
            if cleaned_params != scene.layout.params:
                scene.layout.params = cleaned_params
                changed = True

        object_ids = sorted(
            _collect_scene_object_ids(plan, scene_index),
            key=lambda oid: (plan.objects.get(oid).priority if oid in plan.objects else 999, oid),
        )
        if not object_ids:
            continue

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
                    ValidationErrorItem(f"scenes[{scene_index}].layout.slots.{slot_id} unknown object id: {object_id}")
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

        for action_index, action in enumerate(scene.actions):
            if action.op not in enums["action_ops"]:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}].op not allowed"))
            if isinstance(action, PlayAction) and action.anim not in enums["anims"]:
                errors.append(ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}].anim not allowed"))

            if isinstance(action, PlayAction) and action.anim == "transform":
                src = action.src or (action.targets[0] if len(action.targets) >= 1 else None)
                dst = action.dst or (action.targets[1] if len(action.targets) >= 2 else None)
                if not src or not dst:
                    errors.append(
                        ValidationErrorItem(f"scenes[{scene_index}].actions[{action_index}] transform needs src+dst")
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
