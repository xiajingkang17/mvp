# Layout Schema

## 1. `zones`

每个 scene 都必须先按功能切成多个 zone，并给出精确坐标。

```json
{
  "id": "zone_problem",
  "role": "problem_text",
  "x0": 0.05,
  "x1": 0.48,
  "y0": 0.52,
  "y1": 0.92
}
```

坐标规则：

- 全部使用 `0..1` 的归一化坐标
- 必须满足 `x0 < x1`、`y0 < y1`
- `subtitle` zone 必须固定保留在底部，并且必须严格等于：
  `x0=0.05, x1=0.95, y0=0.02, y1=0.12`
- 其它 zone 不得和 `subtitle` zone 重叠

固定字幕区示例：

```json
{
  "id": "zone_subtitle",
  "role": "subtitle",
  "x0": 0.05,
  "x1": 0.95,
  "y0": 0.02,
  "y1": 0.12
}
```

## 2. `objects`

这里不是列出所有细粒度 object，而是列出“对象组”或“布局对象”。

每个对象条目至少包含：

- `id`
- `kind`
- `zone`

推荐附带：

- `priority`
- `max_width_ratio`
- `max_height_ratio`
- `anchor`
- `placement`
- `stack_order`
- `relative_to`
- `avoid_overlap_with`

示例：

```json
{
  "id": "problem_text_group",
  "kind": "text_block",
  "zone": "zone_problem",
  "priority": 10,
  "max_width_ratio": 0.96,
  "max_height_ratio": 0.92,
  "anchor": "top_left",
  "placement": "stack_down",
  "avoid_overlap_with": ["diagram_group"]
}
```

## 3. `step_layouts`

这部分用于描述“同一个 scene 在不同 step 下，布局参与对象和局部摆放如何变化”。

它不是一整份新的布局合同，而是对 scene 骨架布局的增量说明。

每个 step 条目至少包含：

- `step_id`
- `layout_objects`

推荐附带：

- `hidden_objects`
- `focus_objects`
- `zone_overrides`

示例：

```json
{
  "step_id": "step_02",
  "layout_objects": ["diagram_group", "formula_group"],
  "hidden_objects": ["problem_text_group"],
  "focus_objects": ["formula_group"],
  "zone_overrides": {
    "question_card_group": "zone_top_left_card"
  }
}
```

解释：

- `layout_objects`：这一 step 参与布局计算的对象组
- `hidden_objects`：这一 step 不应参与画面排布的对象组
- `focus_objects`：这一 step 视觉重点对象组
- `zone_overrides`：仅在当前 step 临时改对象组所属 zone

## 4. `global_rules`

至少给出：

- `avoid_overlap`
- `min_gap`
- `formula_stack`
- `subtitle_reserved`

## 5. 输出目标

布局合同必须能回答下面这些问题：

- 这一幕有哪些 zone
- 每个 zone 的坐标是什么
- 题干、图、公式、总结分别放哪
- 哪些对象组不能重叠
- 哪些对象组在不同 step 中参与布局
- 哪些对象组会在某一步切换到新的 zone
