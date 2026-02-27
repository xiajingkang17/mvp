# 锚点与接触规则（硬约束）

1. 只能使用 `anchors_dictionary` 中声明过的锚点名，禁止自造锚点。
2. 两物体接触默认使用“上表面-下表面”锚点配对：
   - 被支撑物体（上方）优先 `bottom_center`。
   - 承载物体（下方）优先 `top_center/top_left/top_right`。
3. 除非题目明确要求“中心重合”，禁止使用 `center-center` 表示接触。
4. 滑块/小球默认：`on_track_pose.args.anchor = "bottom_center"`。
5. 承载体轨道必须定义在可见接触表面，禁止用中心线替代接触面。
6. 木板 `Block` 作为承载体时，上表面轨道优先 `top_left -> top_right`。
7. 斜面 `Wall` 作为承载体时，上表面轨道优先 `high_end -> low_end`。
8. 水平地面 `Wall` 作为承载体时，轨道优先 `start -> end`（左到右）。
9. 若物体跑到承载体下侧，先交换 `anchor_a/anchor_b` 修正轨道方向，不要改成中心线轨道。
10. `attach` 常见安全写法：
    - 箭头尾部贴目标中心：`part_a=arrow, anchor_a=start, part_b=target, anchor_b=center`
11. 禁止输出 `clearance` 字段；接触关系只能由锚点 + 轨道/约束定义。
