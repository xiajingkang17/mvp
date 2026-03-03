# 粒子题运动简表补充规则

如果当前需求是“物理解题视频”，并且题型属于“带电粒子在电场/磁场/复合场中的运动”或其他明显的粒子分段运动问题，请在顶层 JSON 中额外输出一个字段：

- `particle_motion_brief`: object

如果不是这类题，返回空对象 `{}`。

这个字段的目的不是重复完整求解，而是给后续 scene 规划、scene 设计和 motion codegen 提供一份轻量、可直接消费的“粒子怎么动”的真源。

## `particle_motion_brief` 的最小格式

```json
{
  "problem_type": "electromagnetism_particle",
  "questions": [
    {
      "question_id": "q1",
      "question_focus": "第一问求粒子在电场中的运动时间和到达 x 轴时的坐标",
      "motion_phases": [
        {
          "phase_id": "phase_01",
          "from": "P(0,h)",
          "to": "A(x,0)",
          "motion_type": "parabola",
          "analytic": {
            "x_of_t": "v0*t",
            "y_of_t": "h-(qE/2m)t^2"
          },
          "text_prompt": "粒子从 P 点水平射出，在匀强电场中做类平抛运动，直到到达 x 轴"
        }
      ],
      "render_hint": {
        "must_hit_points": ["P", "A"],
        "preserve_region_boundary": true
      }
    }
  ]
}
```

## 字段要求

- `problem_type` 固定写题型；电磁粒子题写 `electromagnetism_particle`。
- `questions` 按题目问法顺序排列。
- `question_id` 使用 `q1 / q2 / q3 ...`。
- `question_focus` 用一句话说明这一问主要在看哪一段运动、求什么量。
- `motion_phases` 用物理分段，而不是动画分段。
- 每个 `motion_phase` 至少要有：
  - `phase_id`
  - `from`
  - `to`
  - `motion_type`
  - `text_prompt`
- 如果这一段能自然坐标化或参数化，就补 `analytic`：
  - 可写 `x_of_t / y_of_t`
  - 或 `y_of_x`
  - 或 `center / radius / start_angle / end_angle / direction`
- 如果某个量已经能由题设和前面解题结果直接确定，就不要继续写成新的随意未知数。
  - 例如能写成 `sqrt(2*m*h/(q*E))`，就不要只写成 `t`
  - 能写成 `v0*sqrt(2*m*h/(q*E))`，就不要只写成 `xA`
  - 能写成具体数值时，优先写具体数值
  - 暂时无法完全化简时，至少写成由已知量组成的确定表达式，而不是额外引入新的占位符
- 如果暂时不方便精确写解析式，也必须写清楚 `text_prompt`，并且描述要足够让下游知道：
  - 从哪里出发
  - 进入哪个区域
  - 这一段属于什么运动
  - 到哪里结束
  - 关键方向或转向是什么
- `render_hint` 只保留少量高价值信息，例如：
  - `must_hit_points`
  - `preserve_region_boundary`
  - `focus_phase_ids`

## 明确限制

- 不要把这部分写成大而全的物理建模文件。
- 不要输出 scene、字幕、镜头、配色、run_time 之类下游信息。
- 不要为了“形式完整”强行给每一段写复杂参数；能解析就解析，不能解析就给高质量文字约束。
- 重点是让后续阶段不再凭感觉猜粒子的轨迹和分段边界。
