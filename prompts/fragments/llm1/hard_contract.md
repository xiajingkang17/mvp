# 硬约束（必须满足）

1. 只能输出 JSON，不要 Markdown，不要代码块，不要解释文字。
2. 根对象必须包含且仅包含：
   - `explanation_full`
   - `global_symbols`
   - `sub_questions`
3. `sub_questions` 不能为空。
4. 每个 `sub_questions[]` 必须包含：
   - `id`
   - `goal`
   - `device_scene_needed`
   - `variable_annotations`
   - `given_conditions`
   - `method_choice`（`method`、`reason`）
   - `derivation_steps`（非空）
   - `result`（至少含 `expression`）
   - `sanity_checks`
   - `scene_packets`（非空）
5. `derivation_steps[].type` 只能是：
   - `equation`
   - `compute`
   - `reasoning`
   - `diagram_note`
6. 每个 `scene_packets[]` 必须包含：
   - `content_items`（1~5 项）
   - `primary_item`（必须出现在 `content_items` 中）
7. `content_items` 和 `primary_item` 只能从以下枚举选择：
   - `hook_question`
   - `goal`
   - `knowns`
   - `diagram`
   - `assumption`
   - `principle`
   - `core_equation`
   - `derive_step`
   - `substitute_compute`
   - `intermediate_result`
   - `conclusion`
   - `check_sanity`
   - `transition`
