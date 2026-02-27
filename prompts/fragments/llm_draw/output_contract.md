# 输出合同

只输出一个严格 JSON 对象，根结构如下：

```json
{
  "version": "0.1",
  "scenes": [
    {
      "id": "S1",
      "composites": [
        {
          "object_id": "o_diagram_xxx",
          "graph": {
            "version": "0.1",
            "space": {
              "x_range": [-10, 10],
              "y_range": [-6, 6],
              "unit": "scene_unit",
              "angle_unit": "deg",
              "origin": "center"
            },
            "parts": [],
            "tracks": [],
            "constraints": [],
            "motions": []
          }
        }
      ]
    }
  ]
}
```

硬性要求：

1. `scenes[].id` 必须来自 `scene_semantic`。
2. `composites[].object_id` 必须是对应 scene 的 `CompositeObject`。
3. `scene_semantic` 给定的 scene/object 集合是不可变白名单：禁止新增、删除、改名。
4. 每个 `graph` 必须完整包含：`version`、`space`、`parts`、`tracks`、`constraints`、`motions`。
5. 轨道类型仅允许 `segment` 与 `arc`，禁止 `line`。
6. 坐标格式硬约束：
   - 组件参数坐标只用 `[x,y]` 或 `[x,y,z]`
   - 轨道数值坐标只用 `x1/y1/x2/y2`、`cx/cy`
   - 轨道局部圆心锚点只用字符串 `center`
7. 禁止输出历史别名或兼容写法（`p1/p2`、`p1_local`、`x1_local`、`a1/a2`、`center:{x,y}` 等）。
8. 对 `segment/arc`：
   - `on_track.timeline` 中的 `s` 必须在 `[0,1]`
   - `on_track_schedule.args.segments[].s0/s1` 必须在 `[0,1]`
9. 对 `state_driver`：
   - `args.mode` 必须是 `"model"`
   - `args.param_key` 必须是 `"tau"`
   - `args.model.kind` 只允许：`ballistic_2d`、`uniform_circular_2d`、`sampled_path_2d`
10. 连续运动切换：同一 `part_id` 从轨道运动切换到 `state_driver` 时优先使用 `args.handoff`。
11. `motions[].timeline` 必须是关键帧对象数组，至少 2 个关键帧，且 `t` 严格递增。
12. 严禁以下格式：
    - `"timeline": {"s": [...]}`
    - `"timeline": [0, 1]`
    - `"args": {"timeline": [...]}`
13. `scene_semantic` 中明确的“在...上/沿...滑动”关系必须在 `graph` 中真实实现（track + constraint + motion 一致）。
14. 禁止输出 `clearance` 字段（任何位置都不允许）。
15. 若语义为“滑块在木板上”，木板轨道必须定义在木板上表面（优先 `top_left -> top_right`），且滑块使用 `anchor: "bottom_center"`。
16. 只输出 JSON，禁止 Markdown 代码块、注释、解释文字。
