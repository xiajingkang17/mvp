# Agent4 视觉映射（与自由布局对齐）
把视觉设计规范映射到 `scene_layout.json`：
1. `elements` -> `layout.placements + keep`。
2. `colors` -> 不在本阶段硬编码（保留对象 style 语义）。
3. `animations` -> `actions`（`play/wait + anim`）。
4. `transitions` -> `keep + 下一场动作衔接`。
5. `camera_movement` -> 当前 2D MVP 忽略，保持 `none` 语义。
6. `duration` -> 体现在 `actions` 的 duration 节奏中。
