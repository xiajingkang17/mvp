# 对象生命周期执行规则（LLM4 必须执行）

当输入 `scene_design` 中存在 `entry_state / steps / exit_state / object_registry` 时，必须按该契约编码，不得忽略。

## 真源划分

1. 所有 scene 都必须从空画面开始，因此 scene 开头真源固定是空集合。
2. `steps[*].object_ops` 与 `steps[*].end_state_objects` 是 step 级显隐真源。
3. 所有 scene 都必须在结尾清空，因此 scene 收场真源固定是空集合。
4. `layout_contract.step_visibility` 只用于布局参与对象，不用于显隐。
5. `scene_plan_scene` 中的 `entry_requirement / handoff_to_next` 只提供叙事语义，不是 object 生命周期真源。

## 执行要求

1. 维护对象注册表，例如 `objects: dict[str, Mobject]`。
2. scene 开头必须执行 `reset_scene(...)`。
3. 所有在 step 中创建并需要后续引用的对象，都必须先 `register_obj(...)`。
4. 同 id 重注册时，`register_obj(...)` 必须先退休旧对象。
5. 对每个 step，严格按 `create/update/remove/keep` 执行。
6. step 结束时，必须清理不在 keep 集合中的对象；清理由 `cleanup_step(...)` 统一执行，不要在 scene 方法里手写循环逐个 `FadeOut` / `remove`。
7. `steps[*].end_state_objects` 必须与 `object_ops.keep` 一致；如有冲突，以 `end_state_objects` 为准理解。
8. 不允许跳过 `cleanup_step(...)`。
9. scene 结束时，必须执行 `cleanup_scene(...)`，并且 keep 集合必须精确等于 `[]`；scene 边界清理统一依赖 helper 内部的批量并行清除。

## 禁止项

- 禁止把 `layout_contract.step_visibility` 当作 show/hide/remove 指令。
- 禁止把所有对象挂到 scene 结束再一次性清空。
- 禁止在 scene 方法里手写 for 循环逐个 `FadeOut`、`Uncreate` 或 `remove` 已注册对象。
- 禁止忽略 `remove` 指令。
- 禁止让任何旧 object 悄悄残留到下一幕。
