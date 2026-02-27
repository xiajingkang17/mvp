# 叙事与旁白（可借鉴 Math-To-Manim 的“叙事创作者”）

你的输出中已经有：

- `narration`: string[]（整段旁白切句）
- `steps[i].narration`: string（每一步旁白）

这里补充一些“可直接提升成片观感”和“提高代码可实现性”的写法约束。

建议原则：

1. 连贯：每个 scene 开头要承接 `transition_in`，结尾要为 `transition_out` 铺垫。
2. 可配音：短句优先，避免一口气读不完的长句；关键结论留 1 秒以上停顿。
3. 讲清楚“你将看到什么”：旁白要能对应到画面中的对象与变化（出现/移动/变形/高亮）。
4. 公式可落地：如果需要展示公式/符号，请给出明确的 LaTeX 内容。
   - 注意：JSON 字符串里反斜杠需要写成 `\\`（例如 `\\frac{a}{b}`）。
   - 重要：LaTeX 必须只包含 ASCII 字符；不要把中文/全角符号/Unicode 希腊字母放进公式里。
     - 错误示例：`\\text{总}`、`α`
     - 正确示例：`\\text{tot}`、`\\alpha`
5. 语气：偏教学向、第二人称更自然（例如“我们先看…”“注意这里…”）。

建议你在 steps 中做到“一句旁白 = 一个明确视觉动作”的对齐：

- 旁白：指出要点（比如“这条边叫 a”）
- visual_description：说明画面如何呈现（比如“在左侧边旁边写上 a，并用绿色高亮”）
- suggested_manim_objects / suggested_animations：列出可实现的对象与动画（比如 Text/MathTex + Write/Indicate）
