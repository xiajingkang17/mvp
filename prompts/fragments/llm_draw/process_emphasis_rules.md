# 过程与运动强调规则

当场景语义包含“过程”（如滑动、分段路径、抛射、圆周、复杂轨迹）时，必须显式建模运动。

1. 过程型场景不能只给静态几何图。
2. 必须用 `graph.motions` 描述完整过程：起始 -> 关键事件 -> 结束。
3. 轨道运动优先使用 `on_track` 或 `on_track_schedule`。
4. 多阶段路径切换必须使用 `on_track_schedule` 分段表达。
5. 同一 `part_id` 在同一时间区间内不要出现冲突 motion。
6. motion、constraint、track 三者语义必须一致，避免“有轨道但 motion 不走该轨道”。
7. 若语义给出“在某物体上运动”，`motion.track_id` 与 `on_track_pose.track_id` 必须一致并共同指向该承载体轨道。
8. 若语义要求“连续运动不中断”，在运动模型切换处优先使用 `state_driver.args.handoff`，避免手写初值导致跳跃。
9. 仅在无法从前段推导时，才允许手写状态模型初值（如 `x0/y0/vx0/vy0`）。