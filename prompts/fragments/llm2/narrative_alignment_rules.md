# 叙事对齐规则（条件片段）

仅在提供 `narrative_plan` 时启用本片段。

1. scene 的主焦点应对齐对应 segment 的 `scene_focus` 与 `visual_intent`。
2. scene 推进顺序尽量对齐 `ordered_concepts`，避免逆序。
3. 若 segment 提供 `transition_hook`，在 `narrative_storyboard.bridge_to_next` 或下一幕 `bridge_from_prev/intro` 中体现衔接语义。
4. 可显式利用 `duration_hint_s` 来规划本 scene 的信息密度（不等于布局动作时长）。
5. 转场描述应可执行，至少说明“从哪个对象过渡到哪个对象、采用何种视觉变化”。
