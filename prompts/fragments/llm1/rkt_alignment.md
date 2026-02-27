# Reverse Knowledge Tree 对齐规则（重点）


若输入中提供了 `concept_tree.json`，必须遵守：

1. `sub_questions` 的教学推进顺序要尽量对齐 `ordered_concepts`（先修在前，目标在后）。
2. 不允许先讲依赖概念之后才补先修概念。
3. `goal` 与 `method_choice.reason` 要体现当前小问在先修链条中的作用。
4. 最后一问必须回到 `analysis.core_concept` 或其等价目标能力。

