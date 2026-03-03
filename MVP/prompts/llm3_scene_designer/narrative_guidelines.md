# 叙事与旁白

你的输出里已经有：

- `narration`: string[]
- `steps[*].narration`: string

这里补充写法约束：

1. 连贯：每个 scene 开头要承接 `entry_requirement`，结尾要为 `handoff_to_next` 铺垫。
2. 配音友好：短句优先，避免一口气读不完的长句。
3. 画面对齐：每句旁白都应对应清晰的视觉动作或视觉焦点变化。
4. `steps[*].narration` 只写单个字符串，不要输出 `string[]`；如果这一句过长，下游运行时会自动按固定字幕区拆成多段顺序显示。
5. 公式可落地：如果需要展示公式，请给出明确的 LaTeX 内容。
6. 教学语气：偏讲解、偏引导，不要写成文学独白。
7. `narration` 用于陪伴式讲解，不应用来替代题目板、当前问题卡、结论板这类需要稳定上屏的信息。
8. 如果本幕承担“整题开场”或“当前问开场”，优先把题目文本放进 `on_screen_text`，而不是只写进 `steps[*].narration`。

推荐做到“一句旁白 = 一个明确视觉动作”：

- 旁白指出要点
- `visual_description` 说明画面如何响应
- `suggested_manim_objects` / `suggested_animations` 给出可实现对象与动画
