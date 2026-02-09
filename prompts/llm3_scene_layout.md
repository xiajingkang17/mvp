# LLM3：scene_layout.json

输入：`scene_draft.json` + 组件/布局/动作枚举。

任务：为每个概念 scene 定稿：

- `layout`：选择 slot 模板（`layout.type`），并把 `slots` 映射到 object id
- `actions`：使用允许的 `op=play/wait` 与允许的 `anim` 组成简短时间线
- `keep`：本 scene 结束后需要保留的对象 id（用于跨 scene 连贯）
- `layout.params`：可选。用于模板参数化（例如 left_right 的 left_ratio，left3_right3/left4_right4 的 row_weights）

【硬性要求】

- 只输出 **一个 JSON 对象**（不要 Markdown，不要代码块，不要解释文字）
- 输出必须是**严格 JSON**（双引号、无尾逗号、true/false/null 用小写）
- 你的输出会被程序用 Python 的 `json.loads(...)` 直接解析：任何非 JSON 文本都会导致任务失败
- 根对象必须包含 `scenes` 数组
- `scenes[].layout` 必须包含 `type` 与 `slots`

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
  "layout": {
    "type": "left_right",
    "slots": {"left":"o1","right":"o2"},
    "params": {"left_ratio": 0.6}
  },
  "actions": [
    {"op":"play","anim":"fade_in","targets":["o1"]},
    {"op":"wait","duration":0.4}
  ],
  "keep": ["o1"]
}
```

约束：

- 仅 slot 模式（不要输出绝对坐标）
- 每个 scene 使用 <= 9 个对象
