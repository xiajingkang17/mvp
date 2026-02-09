# LLM2：scene_draft.json

输入：`problem.md` + `explanation.txt`。

任务：把解题过程拆成概念 scene（每个 2-10 秒）。每个 scene 包含：

- `intent`：一句话说明这一段要讲什么
- `objects`：最多 9 个语义对象（id/type/params/priority/style）
- `notes`：强调点/高亮提示

【硬性要求】

- 只输出 **一个 JSON 对象**（不要 Markdown，不要代码块，不要解释文字）
- 输出必须是**严格 JSON**（双引号、无尾逗号、true/false/null 用小写）
- 你的输出会被程序用 Python 的 `json.loads(...)` 直接解析：任何非 JSON 文本都会导致任务失败
- 根对象必须包含 `scenes` 数组
- `scenes[].objects` 必须是数组；每个 object 必须包含 `id`、`type`
- 不要在这里决定布局或动画

【字段规范】

根对象：

```json
{
  "scenes": [ ... ]
}
```

scene 对象（最小结构）：

```json
{
  "id": "S1",
  "intent": "一句话说明",
  "objects": [
    {"id":"o1","type":"TextBlock","params":{...},"style":{"size_level":"L"},"priority":1}
  ],
  "notes": "可选"
}
```

补充：

- 建议在 `style` 中提供 `size_level`（S/M/L/XL），用于后续布局大小调整
