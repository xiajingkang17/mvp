from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from layout.templates import TEMPLATE_REGISTRY
from schema.scene_plan_models import PlayAction, ScenePlan

from .config import load_app_config, load_enums


@dataclass(frozen=True)
class ValidationErrorItem:
    message: str


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
    return "grid_3x3"


def autofix_plan(plan: ScenePlan) -> bool:
    """
    尽力而为的自动修复，使 LLM 输出可执行。

    MVP 中该策略刻意保持保守：
    - 当 template 缺失/未知时，自动选择一个合法模板
    - 使用 `template.slot_order` 将对象重新分配到合法 slots
    - 删除无效 slots / 去重重复对象
    """

    changed = False

    for scene_index, scene in enumerate(plan.scenes):
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

    for object_id, obj in plan.objects.items():
        if obj.type not in enums["object_types"]:
            errors.append(ValidationErrorItem(f"objects.{object_id}.type not allowed: {obj.type}"))

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

        referenced_ids = _collect_scene_object_ids(plan, scene_index)
        unknown = sorted([x for x in referenced_ids if x not in plan.objects])
        for object_id in unknown:
            errors.append(ValidationErrorItem(f"scenes[{scene_index}] references unknown object id: {object_id}"))

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
