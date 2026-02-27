# 几何绘制与运动编排规则（必须遵守）

你必须输出“可执行 JSON + 详细文字导演说明”。

## 总要求（不要新增 schema 字段）

1. 几何图形怎么画，必须写清。
2. 动图怎么运动，必须写清。
3. 详细说明只能写入已有字段（`notes` 与 `narrative_storyboard`），禁止新增自定义根键。

## 几何图形怎么画（必须输出）

1. 在 `objects` 中明确关键图形对象（type + params + style），不要只放抽象占位对象。
2. 对关键对象必须给：
   - `style.color`（颜色常量）
   - `style.position_hint`（`LEFT/RIGHT/UP/DOWN/ORIGIN` 或坐标文本）
3. 在 `notes` 中必须写清：
   - `geometry_elements:` 本幕图形元素清单
   - `geometry_construction:` 图形构建顺序（先画谁、后画谁、相对位置）
   - `geometry_relations:` 几何关系（平行/垂直/对称/连接/对齐/接触）
4. 若本幕包含 `CompositeObject`，必须在 `notes` 写明“part 使用意图”：
   - 至少列出 2-5 个关键 part.type（来自输入给你的 part 参考清单）
   - 每个 part 要写“是什么 + 何时使用”
   - 地面/斜面语义必须明确写 `Wall`

## 动图怎么运动（必须输出）

1. `narrative_storyboard.animation_steps` 默认至少 4 步；确实极简时可 3 步，但必须覆盖完整教学链路。
2. 每步必须有：`id`、`description`、`targets`、`duration_s`。
3. 每步 `description` 必须包含：
   - 动作原语（优先 `FadeIn`、`FadeOut`、`Create`、`Write`、`Transform`）
   - 作用对象
   - 运动方向/路径或构图变化
   - 起止状态
   - 教学意图（这一步要让学生看懂什么）
4. 转场必须体现在 `bridge_from_prev` 与 `bridge_to_next`，说明“从哪个对象过渡到哪个对象”。

## 镜头、布局与节奏（必须输出）

1. 在 `notes` 中必须写 `camera_movement:`：
   - 非 3D 场景写 `none`
   - 3D 场景必须给 `camera.frame` 运动描述
2. 在 `notes` 中必须写 `layout:`（空间布局与视觉重心）。
3. 在 `notes` 中必须写 `duration:`（本幕总时长，秒）。

## `scene.notes` 固定模板（每个 scene 必须有）

`notes` 至少包含以下 9 行（可换行）：

1. `elements: ...`
2. `colors: ...`
3. `geometry_elements: ...`
4. `geometry_construction: ...`
5. `geometry_relations: ...`
6. `transitions: ...`
7. `camera_movement: ...`
8. `layout: ...`
9. `duration: ...s`

说明：

1. `notes` 必须是可执行导演说明，不是关键词堆砌。
2. 若 3D，必须出现 `camera.frame` 字样并说明镜头动作。
