# 输出合同（必须满足）
1. 只输出一个 JSON 对象，不要 Markdown，不要解释文字。
2. 输出必须可被 `json.loads(...)` 直接解析。
3. 根对象必须包含 `scenes` 数组。
4. `scenes` 必须覆盖 `scene_draft.json` 的全部 scene id，且每个 id 只出现一次。
5. 每个 scene 必须包含：`id`、`layout`、`actions`、`keep`。
6. 每个 `scene.layout` 必须包含：`type=free`、`placements`。
7. free 布局下，`layout.slots` 与 `layout.params` 必须为空对象或省略。
