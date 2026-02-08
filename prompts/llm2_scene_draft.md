# LLM2：scene_draft.json

输入：`problem.md` + `explanation.txt`。

任务：把解题过程拆成概念 scene（每个 2-10 秒）。每个 scene 包含：

- `intent`：一句话说明这一段要讲什么
- `objects`：最多 9 个语义对象（id/type/params/priority/style）
- `notes`：强调点/高亮提示

要求：

- 只输出 **一个 JSON 对象**（不要 Markdown，不要代码块，不要解释文字）
- 不要在这里决定布局或动画

