# 对象语义规则

1. `objects` 只定义“要出现什么对象”，不要写 `CompositeObject.graph` 细节。
2. `objects[].id` 在同一 scene 内必须唯一；跨 scene 尽量复用稳定 id。
3. 公式对象使用 `Formula`，文字说明使用 `TextBlock`。
4. 每个 scene 保持单一主焦点，避免对象过载。
5. 关键对象建议给 `style.color`，颜色常量仅允许：
   `BLUE`、`RED`、`GREEN`、`YELLOW`、`PURPLE`、`ORANGE`、`WHITE`。
6. 位置语义可写入 `style.position_hint`，建议值：
   `LEFT`、`RIGHT`、`UP`、`DOWN`、`ORIGIN` 或坐标文本（如 `[-2,1,0]`）。
7. 可选字段 `modules/roles/new_symbols/is_check_scene` 仅在确有必要时输出。

## 组件清单对齐（强约束）

1. 你会收到一份 `CompositeObject part.type` 参考清单（来自系统注入的已知组件全集），必须按该清单进行语义规划。
2. 不得臆造不存在的 part.type；若语义无法由现有组件表达，再走 `CustomObject`。
3. 矢量箭头语义统一映射为 `Arrow`（例如受力箭头、速度箭头、位移箭头）。
4. 当语义明确“已有组件可表达”时，不要误标成 `CustomObject`。

## 类型边界规则（强约束）

1. `objects[].type` 只能使用顶层类型：
   `TextBlock`、`BulletPanel`、`Formula`、`CompositeObject`、`CustomObject`。
2. `Wall`、`Block`、`Pulley`、`Rope`、`InclinedPlane` 等都属于 `CompositeObject.graph.parts[].type` 参考类型，
   不能直接作为 `objects[].type` 输出。
3. 若需要几何组合，请在 `objects[].type=CompositeObject` 下，通过 `params/notes` 提供绘制意图，而不是写 graph。
4. `CompositeObject` 建议在 `params` 中补充（按需）：
   - `semantic_intent`: 这个组合对象想表达什么
   - `geometry_prompt`: 图形由哪些 part 组成、如何搭建
   - `motion_prompt`: 图形如何运动/变化
   - `must_have_parts`: 必须出现的 part.type 列表
   - `forbidden_parts`: 禁止出现的 part.type 列表
5. 语义中“地面/水平面/斜面/坡面”时，应将 `Wall` 放入 `must_have_parts`，
   并将 `InclinedPlane` 放入 `forbidden_parts`（除非明确要求兼容旧组件）。

## 区域 graph 分配规则（必须遵守）

1. 一个 scene 可以有多个 `CompositeObject`，但每个 `CompositeObject` 只代表一个“视觉区域 graph”。
2. 同一区域内相互耦合的图形（共享轨道、共享约束、运动依赖）必须放在同一个 `CompositeObject`。
3. 禁止把需要引用同一 `part_id/track_id` 的对象拆到不同 `CompositeObject`。
4. 若两个图形区域彼此独立（无共享轨道/约束/运动），才允许拆分为两个 `CompositeObject`。

## CustomObject 触发规则

1. 只有当“现有组件 + CompositeObject.graph”都无法表达时，才使用 `CustomObject`。
2. `CustomObject.params` 必须包含：
   - `custom_role`: `new_component` / `special_motion` / `complex_effect`
   - `draw_prompt`: 图形如何构建（非空字符串）
   - `motion_prompt`: 动画如何运动/变化（非空字符串）
   - `codegen_request`: codegen 标记对象
3. `codegen_request` 结构：
   - `enabled`: bool
   - `scope`: `object` / `motion` / `effect` / `hybrid`
   - `intent`: 非空字符串
   - `kind_hint`: 可选，若给出仅允许 `new_component/special_motion/complex_effect/hybrid/custom`
4. `CustomObject.params` 可选字段：
   - `manim_api_hints`: 字符串数组（例如 `"ValueTracker"`, `"always_redraw"`）
   - `motion_span_s_hint`: 正数秒（建议的运动总时长）
