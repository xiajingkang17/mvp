# 输出硬约束


1. 只能输出一个严格 JSON 对象。
2. 不要 Markdown、不要代码块、不要 JSON 外解释。
3. 根键必须且只能是：

- `analysis`
- `root_id`
- `nodes`
- `edges`
- `ordered_concepts`
- `explanation`

1. `analysis` 必须包含：

- `core_concept`
- `domain`
- `level`（仅可为 `beginner|intermediate|advanced`）
- `goal`

1. `nodes[]` 每项必须包含：

- `id`（稳定 id，如 `n0`, `n1`）
- `concept`（非空）
- `depth`（整数，根节点 `depth=0`）
- `is_foundation`（布尔）
- `rationale`（可选，简短原因）

1. `edges[]` 每项必须包含：

- `from_id`
- `to_id`
- `relation`（固定为 `"requires"`）

边语义：

- `A -> B` 表示 “A 依赖 B（先修）”
- 所以边上深度必须严格增加：`to.depth > from.depth`

1. `ordered_concepts` 约束：

- 必须覆盖所有 `nodes[].concept`，且不重复。
- 顺序必须是 foundation-first、target-last。
- 对任意边 `A -> B`，`B` 必须出现在 `A` 之前。

