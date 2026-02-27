# 力学运动约束模板（滑块轨迹与旋转）

用于 LLM4 代码生成阶段，目标是保证滑块在直线/圆弧/多段组合轨迹上的运动正确、连续、可复现。

## 1. 硬性规则（必须满足）

1) 轨迹参数化必须唯一：

- 直线：`p(s) = p0 + s * (p1 - p0)`
- 圆弧：`p(s) = c + R * [cos(theta0 + s * dtheta), sin(theta0 + s * dtheta)]`
- 每段 `s` 必须单调（`s0 -> s1`），禁止来回跳变。

1) 姿态由轨迹切线决定：

- `t(s) = dp/ds`
- `theta(s) = atan2(t_y, t_x) + angle_offset`
- 禁止用随意 `rotate(...)` 代替切线角。

1) 必须使用接触锚点反推物体中心：

- 设本地接触锚点为 `a_local`（例如 `bottom_center`）
- 世界坐标满足：`center = p(s) - R(theta) * a_local`
- 这样可保证物体不脱轨、不穿轨。

1) 每段结束必须做“强制校正”：

- 强制设置终点位置为该段解析终点
- 强制设置终点角度为该段解析终点角度
- 段间衔接点必须一致（上一段终点 = 下一段起点）。

1) 必须执行数值校验（阈值）：

- 轨道位置误差 `< 1e-2`
- 姿态角误差 `< 2.0` 度
- 段间连续性误差 `< 1e-2`
- 超阈值时必须回退到解析值，不允许继续累积误差。

1) 滚动体附加旋转（仅在需要“滚动不打滑”时）：

- `spin_delta = arc_length / body_radius`
- 最终角度 = 切线角 + 滚动自旋角
- 若场景仅要求“沿轨迹滑动”，则不要叠加滚动自旋。

## 2. 推荐输入契约（motion_contract）

```json
{
  "motion_contract": {
    "track_defs": [
      {"track_id": "t1", "type": "line", "p0": [0, 0], "p1": [3, 1]},
      {"track_id": "t2", "type": "arc", "center": [3, 2], "radius": 1.0, "start_deg": -90, "end_deg": 0, "ccw": true}
    ],
    "segments": [
      {"seg_id": "s1", "part_id": "block_1", "track_id": "t1", "tau0": 0.0, "tau1": 0.5, "s0": 0.0, "s1": 1.0, "angle_mode": "tangent"},
      {"seg_id": "s2", "part_id": "block_1", "track_id": "t2", "tau0": 0.5, "tau1": 1.0, "s0": 0.0, "s1": 1.0, "angle_mode": "tangent"}
    ],
    "anchor_lock": {"part_id": "block_1", "anchor": "bottom_center"},
    "tolerances": {"pos_tol": 0.01, "theta_tol_deg": 2.0, "continuity_tol": 0.01},
    "end_goal": {"type": "anchor_hit", "anchor_id": "P"}
  }
}
```

## 3. 禁止项

- 禁止用随机 `shift`/`rotate` 修运动轨迹。
- 禁止只给起点和终点、缺失中间参数化定义。
- 禁止段间不连续（跳点）仍继续播放。
- 禁止把终点命中要求（如回到 `P`/到达 `Q`）作为“软建议”。

## 4. 输出前自检

- 每段是否有可计算的 `p(s)` 与 `theta(s)`。
- 每段终点是否强制吸附到解析终点。
- 段间连续性误差是否在阈值内。
- 最终是否命中 `end_goal`。
