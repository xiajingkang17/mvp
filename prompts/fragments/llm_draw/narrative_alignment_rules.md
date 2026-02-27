# 叙事对齐规则（仅在提供 `narrative_plan` 时启用）

1. graph 设计要对齐该 scene 的教学焦点与视觉意图。
2. 若叙事强调阶段变化，需在 `motions.timeline` 或 `on_track_schedule.segments` 中体现阶段分界。
3. 相邻 scene 的核心物理实体尽量保持连续命名和连续语义。
4. 用叙事信息决定“谁必须运动、谁保持静态”。
5. 只在 graph 层体现对齐结果，不要新增任何叙事字段。
6. 若语义里明确出现“X 在 Y 上”“X 沿 Y 滑动”“X 从 Y 脱离”，必须落地为可执行几何关系：
   - 为 `Y` 建立轨道（`tracks[].data.part_id = Y`）；
   - `X` 的 `on_track_pose.args.track_id` 必须引用该轨道；
   - `X` 的 `on_track/on_track_schedule` 也必须引用同一承载体轨道。
7. 禁止“语义命名正确但几何引用错误”：例如约束 id 叫 `*_on_board`，实际 `track_id` 却引用地面轨道。
