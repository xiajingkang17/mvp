# 组件合同规则（必须遵守）

前提：输入中已提供两类合同。

- `component contract`：每种 `part.type` 可用的 `params` 与 `anchors`。
- `constraint contract`：每种 `constraints[].type` 可用的 `args` 字段与枚举。

规则：

1. `parts[].params` 只能使用组件合同里该 `part.type` 允许的参数键，禁止臆造参数名。
2. 所有锚点字段（如 `anchor`、`anchor_a`、`anchor_b`、`center`）只能使用组件合同里该 `part.type` 的 `anchors`。
3. 若某 `part.type` 的 `anchors` 为空，禁止猜测锚点；应改用不依赖该锚点的建模方式。
4. 若语义目标与合同冲突，优先满足合同并重构 graph，不要输出合同外字段。
5. `constraints[].args` 只能使用约束合同中对应 `constraints[].type` 允许的参数键。
6. 对于约束合同中带 `enum` 的字段，取值必须严格命中枚举（例如 `on_track_pose.contact_side` 只能是 `outer` 或 `inner`）。
7. 任何不在合同中的键（包括拼写变体）都视为非法，必须删除或改写为合同内表达。
8. 不要用“兼容别名”自创新字段；统一使用合同中的标准字段名。
9. 坐标字段统一格式：
   - 组件参数坐标仅允许 `[x,y]` 或 `[x,y,z]`。
   - 轨道数值坐标仅允许 `x1/y1/x2/y2`、`cx/cy`。
   - 局部圆心锚点仅允许 `center`（字符串锚点名）。
