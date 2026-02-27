# Composite Graph 规则

每个 `graph` 必须“内部自洽、可直接校验通过”。

## 结构要求

1. `tracks[]` 每项格式必须是：`{id, type, data}`。
2. `constraints[]` 每项格式必须是：`{id, type, args, hard}`。
3. `motions[]` 每项格式必须是：`{id, type, args, timeline}`。
4. 禁止把约束参数写在 `params`，必须写在 `args`。
5. `parts[]` 只允许标准字段：`id`、`type`、`params`、`style`、`seed_pose`。
6. 禁止输出 `parts[].anchors`（该字段不在 schema 中）。

## ID 与引用完整性

1. 下列 ID 在各自数组内必须唯一：
   - `parts[].id`
   - `tracks[].id`
   - `constraints[].id`
   - `motions[].id`
2. 所有引用必须指向同一个 `graph` 内已存在的 ID。
3. `part_id`、`part_a`、`part_b`、`from_part_id`、`to_part_id`、`source_part_id`、`target_part_id`
   只能引用 `parts[].id`。
4. `track_id`、`source_track_id`、`target_track_id` 只能引用 `tracks[].id`。
5. 禁止把 scene/object 级 ID 当作 part 引用。
6. 禁止跨 composite 引用 part 或 track。
7. 每个 composite 的 graph 必须“自包含”，不能引用其他 composite 的 `parts[].id`。
8. 若某对象在语义上只表示单个箭头/标记，但无法在本 composite 内找到被附着对象，则不要强行写 `attach` 到外部 part。
9. `tracks[].data.space != "world"` 时，必须提供 `tracks[].data.part_id`，且该 `part_id` 必须属于当前 composite 的 `parts[].id`。
10. 一个 composite 只描述一个区域 graph；跨区域耦合请通过“合并到同一 composite”解决，不要跨引用。
11. 当前阶段禁止改写语义层对象集合：只补全给定 `CompositeObject` 的 graph。

## 约束类型白名单

`constraints[].type` 只允许以下四种：

1. `attach`
2. `midpoint`
3. `distance`
4. `on_track_pose`

禁止输出：`align_angle`、`align_axis` 或任何其他自定义类型。

## `space` 强约束

1. `graph.space` 必须是对象。
2. 若用默认值，可直接写 `"space": {}`。
3. 禁止写 `"space": "local"`、`"space": "world"` 这类字符串。

## 输出前自检（必须全部通过）

1. 每个 `constraint.args.part_*` 都能在 `parts` 中找到。
2. 每个 `constraint.args.track_id` 都能在 `tracks` 中找到。
3. 不存在白名单外的 `constraints[].type`。
4. 所有 composite 的 `graph.space` 都是对象类型。
5. 每个 `motions[].timeline` 都是关键帧对象数组（`[{t, ...}, ...]`），不是字典或数值数组。
6. 每个 `motions[].timeline` 至少 2 个关键帧，且 `t` 严格递增。

## 语义关系落地（强制）

1. 若 `scene_semantic` 明确写“某物在某承载体上（例如滑块在木板上）”，则该物体必须贴在承载体轨道上，不得贴到其他轨道。
2. 若语义写“在某承载体上滑动”，必须同时满足：
   - `on_track_pose` 贴轨目标为该承载体轨道；
   - `on_track/on_track_schedule` 运动轨道也为该承载体轨道。
3. 同一语义关系中的 `subject/carrier` 必须在几何引用上严格一致，禁止仅靠 id 命名表达关系。
4. 当 scene 同时包含 `ground` 与 `board` 时，若语义写“滑块在木板上”，滑块轨道承载体必须是 `board`，不能是 `ground`。
