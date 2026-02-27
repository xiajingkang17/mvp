# 通用力学绘图协议：校验规则

以下规则建议作为硬校验：

1. JSON 结构合法，约束字段统一使用 `args`。
2. 所有 `part_id/track_id` 引用必须存在。
3. 所有锚点名必须在组件锚点字典中存在。
4. 连接关系必须通过 `attach` 明确表达。
5. 存在可动物体时，必须有 `on_track_pose` 或 `motions.on_track/on_track_schedule`。
6. `on_track_schedule` 必须有连续分段和有效 timeline。
7. `Wall.angle` 范围必须在 `[0, 90]`，方向由 `rise_to` 表达。

说明：`align_angle`/`align_axis` 已移除，不参与校验。
