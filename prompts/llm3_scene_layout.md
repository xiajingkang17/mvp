# LLM3：scene_layout.json

输入：`scene_draft.json` + 组件/布局/动作枚举。

任务：为每个概念 scene 定稿：

- `layout`：选择 slot 模板（`layout.type`），并把 `slots` 映射到 object id
- `actions`：使用允许的 `op=play/wait` 与允许的 `anim` 组成简短时间线
- `keep`：本 scene 结束后需要保留的对象 id（用于跨 scene 连贯）

要求：

- 只输出 **一个 JSON 对象**（不要 Markdown，不要代码块，不要解释文字）

约束：

- 仅 slot 模式（不要输出绝对坐标）
- 每个 scene 使用 <= 9 个对象

