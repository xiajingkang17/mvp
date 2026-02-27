# 运动规则（必须遵守）

## 允许的 motion.type

1. `on_track`：单轨道运动。
2. `on_track_schedule`：多轨道分段运动。
3. `state_driver`：无轨道轨迹驱动运动。

## timeline 通用规则

1. `motions[].timeline` 必须是关键帧对象数组：`[{"t": number, "<param_key>": number}, ...]`。
2. 至少 2 个关键帧。
3. 所有关键帧 `t` 必须严格递增。
4. `timeline` 必须放在 `motions[].timeline`，禁止放在 `args.timeline`。

## on_track

1. 必须包含：`args.part_id`、`args.track_id`。
2. `args.track_id` 必须引用 `segment` 或 `arc`。
3. `param_key` 默认 `s`，所有关键帧 `s` 必须在 `[0,1]`。

## on_track_schedule

1. 必须包含：`args.part_id`、`args.segments`。
2. 每段必须有：`track_id`、`u0`、`u1`、`s0`、`s1`。
3. `track_id` 必须引用 `segment` 或 `arc`。
4. 每段要求：`u1 > u0`，并且段间连续（后一段 `u0` 等于前一段 `u1`）。
5. 所有段 `s0/s1` 必须在 `[0,1]`。
6. `param_key` 默认 `u`，timeline 的 `u` 必须在 `[0,1]`。

## state_driver（无轨道）

1. 必须包含：`args.part_id`、`args.mode="model"`、`args.model`。
2. `args.param_key` 固定使用 `tau`。
3. timeline 的 `tau` 建议归一化到 `[0,1]`。
4. `args.model.kind` 只允许：
   - `ballistic_2d`
   - `uniform_circular_2d`
   - `sampled_path_2d`

### 连续运动切换（重点）

1. 当同一 `part_id` 从轨道运动（`on_track`/`on_track_schedule`）切换到 `state_driver` 时，优先使用 `args.handoff` 自动接续。
2. 推荐写法：
   - `handoff.from_time` = 前一段运动结束时刻
   - `handoff.position = true`
   - 若还要速度连续，再设 `handoff.velocity = true`
3. 优先级：`handoff` > 手写 `x0/y0/vx0/vy0`。
4. 仅当不存在可接续前段时，才手写 `x0/y0/vx0/vy0`。
5. 禁止“无 handoff 且手写坐标明显不连续”导致切换跳跃。

### ballistic_2d 参数

1. `model.params` 必须包含：`vx0`、`vy0`。
2. 若未使用 `handoff.position`，还必须提供：`x0`、`y0`。
3. `g` 可选。

### uniform_circular_2d 参数

1. `model.params` 必须包含：`cx`、`cy`、`r`、`omega`。
2. `phi0` 可选。

### sampled_path_2d 参数（复杂轨迹兜底）

1. `model.params.samples` 必须是数组，长度至少 2。
2. 每个样本必须是：`{"tau": number, "x": number, "y": number}`。
3. `tau` 必须严格递增，且建议在 `[0,1]`。
4. state_driver 的 timeline `tau` 必须落在该 samples 的 `tau` 覆盖范围内。
5. 复杂轨迹（先圆周再圆周、椭圆、任意曲线）统一用该 kind。

## 禁止项

1. 禁止未声明的 `motion.type`。
2. 禁止空 `timeline`。
3. 禁止同一 `part_id` 在同一时间区间被多个 motion 同时驱动。