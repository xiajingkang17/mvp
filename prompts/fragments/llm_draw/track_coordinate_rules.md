# 轨道坐标与方向规则（硬约束）

1. 只允许 `tracks[].type` 为 `segment` 或 `arc`，禁止 `line`。
2. 组件参数里的坐标仅允许数组：`[x, y]` 或 `[x, y, z]`。
3. 轨道数值坐标只允许：
   - 线段：`x1/y1/x2/y2`
   - 圆弧：`cx/cy`（配合 `radius/start/end`）
4. 轨道局部圆心锚点只允许：`center`（字符串锚点名）。
5. 局部 `segment` 必须写：`part_id + anchor_a + anchor_b`；禁止 `x1/y1/x2/y2`。
6. 世界 `segment` 必须写：`x1/y1/x2/y2`；禁止 `part_id/anchor_a/anchor_b`。
7. `arc` 只允许字段：`space`、`part_id`、`center`、`cx`、`cy`、`radius`、`start`、`end`。
8. 局部 `arc`：必须有 `part_id`，并且 `center`（锚点）或 `cx/cy`（局部数值）二选一。
9. 世界 `arc`：必须有 `cx/cy`，且禁止 `part_id` 与 `center`。
10. 轨道语义与运动语义分离：`tracks` 只定义几何，`constraints/motions` 只引用 `track_id`。
11. 对 `segment/arc`：
    - `on_track.timeline[*].s` 必须在 `[0,1]`
    - `on_track_schedule.args.segments[*].s0/s1` 必须在 `[0,1]`
12. 禁止输出历史别名或兼容写法（例如 `p1/p2`、`p1_local`、`x1_local`、`a1/a2`、`center:{x,y}`）。
13. 禁止使用 `clearance` 参数（项目已移除）。
14. “在某物体上滑动”时，`on_track_pose.track_id` 与对应 `motion.track_id` 必须一致。
15. 方向硬规则（防止翻到承载体下侧）：
    - 木板 `Block` 上表面：`top_left -> top_right`
    - 斜面 `Wall` 上表面：`high_end -> low_end`
    - 水平地面 `Wall` 上表面：`start -> end`（优先左到右）
16. 滑块/小球默认使用 `on_track_pose.args.anchor = "bottom_center"`。
