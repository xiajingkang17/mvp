# LLM3：生成 `scene_layout.json`（布局与动作层）

输入：`scene_draft.json` + 模板/动作枚举 + 模板槽位目录 + 参数规范。  
任务：只做布局与动作编排，不修改对象语义，不发明新对象。

## 输出合同（必须满足）

只输出一个 JSON 对象，根结构如下：

```json
{
  "scenes": [
    {
      "id": "S1",
      "layout": {
        "type": "left_right",
        "slots": {"left": "o_diagram", "right": "o_text"},
        "params": {"slot_scales": {"left": {"w": 0.95, "h": 0.9}}}
      },
      "actions": [
        {"op": "play", "anim": "fade_in", "targets": ["o_diagram"]},
        {"op": "wait", "duration": 0.4},
        {"op": "play", "anim": "write", "targets": ["o_text"]}
      ],
      "keep": ["o_diagram", "o_text"],
      "roles": {"o_diagram": "diagram", "o_text": "support_eq"}
    }
  ]
}
```

## 全局硬约束（必须）

1. 只输出 JSON；不要 Markdown、不要代码块、不要解释文字。
2. 输出必须可被 `json.loads(...)` 直接解析。
3. 根对象必须包含 `scenes` 数组。
4. `scenes` 必须覆盖 `scene_draft.json` 的所有 scene id，且每个 id 只出现一次。
5. 每个 scene 必须包含：`id`、`layout`、`actions`、`keep`。
6. 不要输出绝对坐标；只能使用模板 slot 布局。
7. 不能新增 object id；只能引用 `scene_draft.json` 中已有对象。
8. `slots/actions/keep/roles` 中出现的每个 object id 都必须存在。

## layout 约束（必须）

1. `layout.type` 只能从输入给定的允许列表中选择。
2. `layout.slots` 的 key 必须来自“模板槽位目录”。
3. `layout.slots` 的 value 必须是合法 object id。
4. `layout.params` 只允许 `slot_scales`。
5. `slot_scales` 结构必须是：
   `{ "<slot_id>": {"w": 0.2~1.0, "h": 0.2~1.0} }`
6. 禁止输出其它模板参数（如 `left_ratio`、`row_weights` 等）。

## actions 约束（必须）

1. `op` 只能是 `play` 或 `wait`。
2. `wait` 必须有 `duration`（`>= 0`）。
3. `play.anim` 只能从允许 anim 列表中选。
4. 对 `fade_in/fade_out/write/create/indicate`：
   `targets` 必须是非空数组。
5. 对 `transform`（最关键）：
   必须满足其一：
   - 显式提供 `src` 和 `dst`；
   - 或 `targets` 至少 2 个（第1个作 `src`，第2个作 `dst`）。
6. 严禁输出这种非法形式：
   `{"op":"play","anim":"transform","targets":["only_one"]}`
7. 若无法确定合法 `transform` 参数，改用：
   `write` / `fade_in` / `fade_out`，不要硬用 `transform`。

## keep 与 roles 约束（强烈建议按此输出）

1. `keep` 仅保留下一段仍需在屏幕上可见的对象。
2. 若输出 `roles`，只保留本 scene 实际使用到的对象（在 `slots/actions/keep` 中出现）。
3. 若 `scene_draft` 中某角色对象在本 scene 不使用，不要把它放进本 scene 的 `roles`。
4. 如果提供 `goal/modules/new_symbols/is_check_scene`，必须与本 scene 行为一致。

## 教学与排版策略（应尽量满足）

1. 若 `scene_draft` 提供 `roles`，优先按角色分槽位：
   - `diagram` 单独占主槽；
   - `core_eq` 与 `support_eq` 分离并按阅读顺序排列；
   - `conclusion` 与 `check` 尽量单独留位。
2. 若提供 `pedagogy_plan.cognitive_budget`，尽量遵循同屏负荷限制。
3. 一个 scene 尽量只保留一个视觉主焦点，避免堆叠感。

## 模板选型建议

- 1-2 对象：`hero_side` 或 `left_right`
- 3-4 对象：`grid_2x2`
- 5-6 对象：`left3_right3`
- 7-8 对象：`left4_right4`
- 9 对象：`grid_3x3`

## 输出前自检（仅内部，不要输出）

1. 所有 scene id 是否齐全且不重复。
2. `layout.type` 是否合法。
3. `slots` 键名是否属于对应模板。
4. `slots/actions/keep/roles` 里的 object id 是否全部存在。
5. `layout.params` 是否只含 `slot_scales`。
6. 所有 `transform` 是否满足 `src+dst` 或 `targets>=2`。
