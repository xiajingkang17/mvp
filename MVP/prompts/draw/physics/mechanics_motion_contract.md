# 力学运动契约模板（step 主导版）

用于 LLM3/LLM4 阶段，目标是让 `motion_contract` 同时承担：

- 可执行约束：轨迹参数化、step 内运动段、姿态、锚点锁定、误差校验
- 结构约束：运动必须明确挂到某个 `step_id`，不能再自带一套独立于 `steps` 的全局时间轴

`motion_contract` 是唯一运动真源；不要再并行输出第二套 `motion_constraints`。

## 1. 硬性规则（必须满足）

1) `steps` 是主时间轴：

- 先由 `steps[*]` 决定“何时动”
- `motion_contract` 只定义“这个 step 里怎么动”
- 不要再用一套独立于 `steps` 的全局时间区间控制整幕运动

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
    "tracked_parts": ["block_1"],
    "anchor_points": ["P", "Q", "L1", "L2"],
    "track_defs": [
      {"track_id": "t1", "type": "line", "p0": [0, 0], "p1": [3, 1]},
      {"track_id": "t2", "type": "arc", "center": [3, 2], "radius": 1.0, "start_deg": -90, "end_deg": 0, "ccw": true}
    ],
    "step_motions": [
      {
        "step_id": "step_02",
        "segments": [
          {
            "seg_id": "s1",
            "part_id": "block_1",
            "track_id": "t1",
            "from_anchor": "P",
            "to_anchor": "L2",
            "path_type": "line",
            "must_end_at_anchor": true,
            "s0": 0.0,
            "s1": 1.0,
            "angle_mode": "tangent",
            "duration_ratio": 0.4
          },
          {
            "seg_id": "s2",
            "part_id": "block_1",
            "track_id": "t2",
            "from_anchor": "L2",
            "to_anchor": "Q",
            "path_type": "arc",
            "must_end_at_anchor": true,
            "s0": 0.0,
            "s1": 1.0,
            "angle_mode": "tangent",
            "duration_ratio": 0.6
          }
        ]
      },
    ],
    "anchor_lock": {"part_id": "block_1", "anchor": "bottom_center"},
    "tolerances": {"pos_tol": 0.01, "theta_tol_deg": 2.0, "continuity_tol": 0.01},
    "end_goal": {
      "type": "anchor_hit",
      "anchor_id": "Q"
    }
  }
}
```

## 3. 字段最低要求

- 顶层必须有 `anchor_points`，列出后续会引用的语义锚点。
- 顶层必须有 `step_motions`，并且每个运动 step 都必须显式写出 `step_id`。
- 每个 `segment` 必须有：
  - `from_anchor`
  - `to_anchor`
  - `path_type`
  - `must_end_at_anchor`
- 若一个 step 中有多段运动，建议用 `duration_ratio` 表示该 step 内的相对时长分配。

## 4. 禁止项

- 禁止用随机 `shift`/`rotate` 修运动轨迹。
- 禁止只给起点和终点、缺失中间参数化定义。
- 禁止继续使用顶层 `segments` 搭配全局 `tau0 / tau1` 作为独立时间轴。
- 禁止段间不连续（跳点）仍继续播放。
- 禁止把终点命中要求（如回到 `P`/到达 `Q`）作为“软建议”。
- 禁止让 `motion_contract` 脱离 `steps` 单独决定“什么时候动”。

## 5. 输出前自检

- 每段是否有可计算的 `p(s)` 与 `theta(s)`。
- 每个运动段是否都明确挂到了某个 `step_id`。
- 每段终点是否强制吸附到解析终点。
- 段间连续性误差是否在阈值内。
- 最终是否命中 `end_goal`。
