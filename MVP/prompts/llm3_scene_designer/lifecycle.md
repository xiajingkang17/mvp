# 生命周期契约

LLM3 必须显式设计：

- scene 开场状态
- step 结束状态
- scene 收场状态

目标是杜绝旧对象无控制残留。

## 真源划分

1. `entry_state.objects_on_screen` 是 scene 开场真源。
2. `steps[*].object_ops` 与 `steps[*].end_state_objects` 是 step 级真源。
3. `exit_state.objects_on_screen` 是 scene 收场真源。
4. `layout_contract` 只负责布局，不负责生命周期。

## 强制规则

1. 所有对象必须先在 `object_registry` 中定义，再在 `steps[*]` 中引用。
2. 每个 step 必须提供 `create/update/remove/keep` 四个列表。
3. `object_ops.keep` 必须与 `end_state_objects` 完全一致。
4. 未进入该 step `end_state_objects` 的对象，必须在该 step 结束前退出。
5. 每个 scene 都必须从空画面开始，因此 `entry_state.objects_on_screen` 固定为 `[]`。
6. 每个 scene 都必须在结尾清空，因此 `exit_state.objects_on_screen` 固定为 `[]`。
7. 禁止把标题、旧辅助线、临时高亮、字幕、推导面板累积到后续 scene。

## 参考结构

```json
{
  "object_registry": [
    {"id": "title_main", "kind": "text", "role": "title", "lifecycle_role": "ephemeral"},
    {"id": "eq_1", "kind": "math", "role": "formula", "lifecycle_role": "evolving_anchor"},
    {"id": "block_1", "kind": "shape", "role": "main_visual", "lifecycle_role": "persistent_anchor"}
  ],
  "entry_state": {
    "objects_on_screen": [],
    "visual_focus": "开场焦点"
  },
  "steps": [
    {
      "step_id": "step_01",
      "object_ops": {
        "create": ["title_main"],
        "update": [],
        "remove": [],
        "keep": ["block_1", "title_main"]
      },
      "end_state_objects": ["block_1", "title_main"]
    }
  ],
  "exit_state": {
    "objects_on_screen": [],
    "handoff_intent": "给下一幕的叙事承接"
  }
}
```
