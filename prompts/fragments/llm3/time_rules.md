# 动画时间规则（必须满足）

1. 若某 scene 含有 `CompositeObject.params.graph.motions`，该 scene 必须可驱动动画时间推进。
2. 这类 scene 中每个 `play` 必须显式给 `duration > 0`。
3. 场景时长覆盖规则：
   `sum(wait.duration + play.duration)` 必须不小于所需 motion 时间跨度。
4. 不要把一个连续物理过程拆成多个静态 scene 来伪造运动。
