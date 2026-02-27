# 对齐规则（重点）

1. `ordered_concepts` 必须与 `concept_tree.ordered_concepts` 保持一致（或语义一致且同序）。
2. `segments` 的 `concept_ref` 可以按叙事节奏自由编排（允许先现象后原理），但每个 `concept_ref` 必须出现在 `ordered_concepts` 中。
3. 最后一个 segment 必须落在目标概念（`analysis.target_concept`）。
4. 能映射到 `teaching_plan.sub_questions` 的 segment，优先填 `sub_question_id`。
5. 每个 segment 的 `narration` 要能直接指导后续视觉生成，避免空泛。
