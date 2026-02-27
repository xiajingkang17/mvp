# 输出合同

只输出一个 JSON 对象，根结构如下：

```json
{
  "version": "0.1",
  "scenes": [
    {
      "id": "S1",
      "intent": "...",
      "goal": "...",
      "notes": "...",
      "objects": [],
      "narrative_storyboard": {}
    }
  ]
}
```

硬约束：

1. `scenes[]` 必须非空。
2. 每个 scene 必须包含 `id`、`intent`、`goal`、`notes`、`objects`、`narrative_storyboard`。
3. `objects[]` 内若 `type=CompositeObject`，`params` 里不能出现 `graph`。
4. `objects[].type` 只能使用顶层类型：`TextBlock`、`BulletPanel`、`Formula`、`CompositeObject`、`CustomObject`。
5. `Wall/Block/Pulley/...` 仅可作为 `CompositeObject` 的 part 语义提示，不得出现在 `objects[].type`。
6. 详细文字说明必须写入已有字段（尤其 `notes` 与 `narrative_storyboard`），不要新增自定义根键。
7. 不要输出 Markdown、解释性前后缀或代码块。
8. 每个 scene 的 `notes` 必须覆盖：`geometry_elements`、`geometry_construction`、`geometry_relations`、`transitions`、`camera_movement`、`layout`、`duration`。
9. 若使用 `CustomObject`，`params` 必须包含 `custom_role`、`draw_prompt`、`motion_prompt`、`codegen_request`。
10. `codegen_request` 必须包含：

- `enabled`: bool
- `scope`: `object | motion | effect | hybrid`
- `intent`: non-empty string
- `kind_hint`: optional，若给出只能是 `new_component | special_motion | complex_effect | hybrid | custom`

11. 必须遵守输入中提供的完整 part 参考清单；禁止输出清单外的 part.type 语义建议。
