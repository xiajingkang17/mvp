# 生命周期契约（LLM3 必须输出）

你必须显式输出对象生命周期信息，避免“旧对象一直残留到 scene 结束”。

## 顶层必须新增字段

```json
{
  "object_manifest": [
    {"id": "title_main", "kind": "text", "role": "title"},
    {"id": "eq_1", "kind": "math", "role": "formula"},
    {"id": "block_1", "kind": "shape", "role": "main_visual"}
  ],
  "lifecycle_contract": {
    "default_policy": "remove_unkept_after_step",
    "step_visibility": [
      {"step": 1, "create": ["title_main"], "update": [], "remove": [], "keep": ["title_main"]},
      {"step": 2, "create": ["eq_1"], "update": ["title_main"], "remove": [], "keep": ["title_main", "eq_1"]},
      {"step": 3, "create": ["block_1"], "update": ["eq_1"], "remove": ["title_main"], "keep": ["eq_1", "block_1"]}
    ],
    "scene_end_keep": ["block_1"]
  }
}
```

## 强制规则

1) 所有对象必须先在 `object_manifest` 定义，再在 `step_visibility` 中引用。  
2) 每个 step 必须提供 `create/update/remove/keep` 四个列表（可为空）。  
3) 未进入 `keep` 的对象，必须在该 step 末尾移除（或明确进入下一 step 的 `remove`）。  
4) `scene_end_keep` 只能保留极少关键对象（建议 <= 3），并与输入中的 `carry_over` 保持一致。  
5) 禁止把公式面板、标题、旧辅助线无限累积到后续步骤。  
