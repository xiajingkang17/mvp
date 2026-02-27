# 硬约束

1. 只能输出 JSON，不要 Markdown、不要代码块、不要解释。
2. 根键必须且只能是：
   - `analysis`
   - `global_arc`
   - `ordered_concepts`
   - `segments`
   - `style_guide`
   - `explanation`
3. `analysis` 必须包含：
   - `target_concept`
   - `narrative_goal`
   - `audience_level`（`beginner|intermediate|advanced`）
4. `segments` 不能为空。每个 `segments[]` 必须包含：
   - `id`
   - `concept_ref`
   - `sub_question_id`（可空）
   - `title`
   - `narration`
   - `visual_intent`
   - `key_equations`（可空数组）
   - `scene_focus`（必须来自教学内容枚举）
   - `transition_hook`（可空）
   - `duration_hint_s`（整数，建议 8~30）
5. `scene_focus` 枚举：
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
