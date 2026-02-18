# 通用力学绘图协议：装配层（无 align）

## 1. 装配目标

- 连接处点重合、无断开、无漂移。
- 优先使用 `attach` + 合法锚点，不使用 `align_angle/align_axis`。

## 2. 连接规则

1. 每个连接点至少一条 `attach`。
2. 轨道骨架（斜面/平面/弧面）建议统一 `attach.args.rigid=true`，形成刚体组。
3. 连接关系建议按链路从上游到下游表达，并配合 `mode` 控制谁移动（推荐 `b_to_a` 固定上游）。

## 3. 常见连接模式

### 3.1 线段-线段

- 端点 `attach`

### 3.2 线段-圆弧

- 线段端点与弧端点 `attach`
- 圆弧方向由 `ArcTrack.start_angle/end_angle` 表达，不依赖 align

### 3.3 几何辅助约束

- `midpoint`：中点关系
- `distance`：两点距离关系

## 4. 锚点合法性

- 锚点名称必须来自 `anchors_dictionary`。
- 禁止未知锚点回退到 `center`。
