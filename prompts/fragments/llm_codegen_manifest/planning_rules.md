# 规划规则

1. 每个目标 `CustomObject` 必须且只能出现一次。
2. `object_id` 是不可变输入：禁止改名、合并、拆分。
3. `code_key` 必须是稳定 snake_case。
4. `spec` 必须严格使用 DSL 骨架：`dsl_version/kind/geometry/style/motion/effects/meta`。
5. `spec` 内禁止 Python 代码、Markdown、大段自然语言。
6. 有连续运动时必须给 `motion_span_s` 正数；无连续运动时填 `null`。

## 运动规划（关键）
1. 高频标准运动优先：
   - `ballistic_2d`
   - `uniform_circular_2d`
2. 复杂轨迹统一走：
   - `sampled_path_2d`
   - 用 `samples[{tau,x,y}]` 表达路径
3. 当需要自动回填到 `scene_plan` 时，必须输出 `spec.motion.driver`。
4. `spec.motion.driver.target_object_id` 必须写清楚目标 `CompositeObject`。
5. `spec.motion.driver.part_id` 必须写目标 graph 内部真实 part id。
6. `spec.motion.driver.timeline` 的 `tau` 与 `sampled_path_2d.samples.tau` 保持同一参数域（建议 `[0,1]`）。

## 视觉一致性
1. 轨迹显示和运动驱动必须共用同一份轨迹数据来源（避免“画出来的轨迹”和“实际运动”不一致）。
2. 数学对象颜色保持一致，在 `style.color_map` 明确声明。
3. 至少给出起始态、变化态、收束态三段时间节奏。
