# 通用力学绘图协议：运动层

## 1. 目标

让可动物体沿轨道稳定运动，并支持多轨道分段切换。

## 2. 关键约束

- `constraints.on_track_pose`：静态贴轨（`track_id + s`）。
- `motions.on_track`：单轨道动画。
- `motions.on_track_schedule`：多轨道分段动画。

## 3. 建议流程

1. 先保证骨架通过 `attach`（必要时 `rigid=true`）装配稳定。
2. 再用 `on_track_pose`/`motion` 绑定可动物体。
3. 跨轨道切换必须用 `on_track_schedule`，并保证切换段连续。
