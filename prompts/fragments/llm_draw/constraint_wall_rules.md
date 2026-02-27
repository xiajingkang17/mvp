# 约束与 Wall 规则（必须遵守）

## 约束字段示例

正确：

```json
{
  "id": "c_attach_1",
  "type": "attach",
  "args": {
    "part_a": "p_rod",
    "anchor_a": "end",
    "part_b": "p_arc",
    "anchor_b": "start"
  },
  "hard": true
}
```

错误（禁止）：

```json
{
  "id": "c_attach_1",
  "type": "attach",
  "params": {
    "part_a": "p1",
    "part_b": "p2"
  }
}
```

### Wall 参数语义

1. `Wall.params.angle` 仅表示坡度大小，范围必须是 `0 <= angle <= 90`。
2. `Wall` 的“向左升高/向右升高”必须用 `Wall.params.rise_to` 表达，取值只能是 `"left"` 或 `"right"`。
3. 不要用 `angle > 90` 或负角度来表达方向。

### 地面/斜面组件约束

1. 任何语义为“地面/水平面/底面/斜面/坡面”的 `part`，类型必须使用 `Wall`。
2. `Rod` 只用于细杆、连接杆或参考线，禁止把 `Rod` 当作地面或斜面。
3. 水平地面请用 `Wall`（例如 `angle=0`，`rise_to` 明确给出 `"left"` 或 `"right"`）。
