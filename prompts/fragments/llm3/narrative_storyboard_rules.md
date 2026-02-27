# 叙事驱动分镜规则（条件片段）

仅在提供 `narrative_plan` 时启用本片段。

1. 把每个 scene 当作分镜段落，不要输出随机动作列表。
2. 每个 scene 的 actions 至少覆盖以下四段中的三段：
   - 开场（引入主焦点）
   - 建立（展示结构或关系）
   - 强调（`indicate` 或 `transform`）
   - 转场（为下一 scene 留钩子）
3. scene 主焦点应与角色语义一致（如 `diagram/core_eq/conclusion/check`）。
4. 若存在 narrative 的 `scene_focus`，优先采用对应节拍：
   - `diagram`：`create/fade_in -> indicate -> wait`
   - `core_equation`：`write -> indicate(关键项) -> wait`
   - `derive_step/substitute_compute`：`write/transform -> wait`
   - `conclusion/check_sanity`：`indicate -> write(结论文本) -> wait`
5. 若提供 `duration_hint_s`，在满足 motion 覆盖前提下尽量贴近该时长。
6. 对跨 scene 持续对象，优先用 `transform/indicate` 做连续衔接，避免“先消失再出现”。
