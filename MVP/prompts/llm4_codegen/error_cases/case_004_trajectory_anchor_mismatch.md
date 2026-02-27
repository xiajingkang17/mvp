# 历史错误案例 004：粒子轨迹与目标锚点不一致

## 真实问题（已发生）

- 运动轨迹能渲染，但逻辑不闭合：例如“回到 P”场景末尾粒子并未回到 `P_point`。
- 多段路径首尾不接，导致轨迹跳变或看起来“不对”。

## 根因

- 路径按“目测”拼接，没有先定义锚点与段间约束。
- 圆弧参数（半径/起始角/转角）与边界位置不匹配。

## 生成硬约束（必须遵守）

1) 先定义并统一使用锚点：`P_pos/Q_pos/L1_y/L2_y/L3_y/L4_y`。
2) 每段路径都要显式声明起点和终点，且与粒子当前位置连续。
3) 关键目标必须在 scene 末尾满足：
   - “回到 P” -> 粒子位于 `P_point`
   - “到达 Q” -> 粒子位于 `Q_point`
4) 若圆弧难以参数化闭合，优先用 `ArcBetweenPoints` 保证几何可达，再补充标注说明。

## 推荐实现要点

```python
start = self.particle.get_center()
target = self.P_point.get_center()
path = Line(start, target)  # 保证起终点可控
self.play(MoveAlongPath(self.particle, path))
```

## 输出前自检清单（必须执行）

- 每段 `MoveAlongPath` 的起点是否等于当前粒子位置？
- 场景目标锚点是否在末尾命中（P/Q）？
- 是否删除了自相矛盾的长注释与“猜测式路径”？
