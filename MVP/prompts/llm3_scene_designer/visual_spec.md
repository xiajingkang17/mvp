# 视觉规范（可借鉴 Math-To-Manim 的“视觉设计师”）

为了让后续代码生成更稳定、全片更一致，建议你在输出 JSON 顶层额外补充一个字段：`visual_spec`。

`visual_spec` 的目标：

- 把“本 scene 的视觉设计决定”显式写出来（元素、配色、布局、转场、节奏）
- 让代码生成器尽量少猜测

建议结构（示例，仅供参考，可按需精简/扩展）：

```json
{
  "visual_spec": {
    "elements": ["triangle", "label_a", "label_b", "equation_main"],
    "colors": {
      "triangle": "BLUE",
      "equation_main": "YELLOW",
      "label_a": "GREEN"
    },
    "layout": "主图居中偏左；关键公式右上；结论底部居中",
    "transitions": {
      "in": "承接上一段：保留右三角形并淡入标签",
      "out": "为下一段铺垫：保留三条边标注与公式"
    },
    "camera_movement": "none",
    "duration_s": 18
  }
}
```

约束与建议：

- 颜色：优先使用 Manim 颜色常量（例如 BLUE/RED/GREEN/YELLOW/ORANGE/WHITE），避免过多颜色导致噪音。
- 位置：尽量用 Manim 常见方位词描述（LEFT/RIGHT/UP/DOWN/ORIGIN）或“相对关系”（next_to/to_edge/shift）。
- 一致性：若前后 scene 摘要里出现同一关键主线，请尽量复用这些关键对象（同一个元素名称/含义保持一致），不要每幕换一套命名与配色。
- 镜头：默认 `camera_movement="none"`；除非明确需要 3D，否则不要引入 ThreeDScene 相关设定。
