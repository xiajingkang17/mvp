# JSON 结构示例（仅示例形状）

{
  "explanation_full": "完整解题过程文本",
  "global_symbols": [
    {"name": "m", "meaning": "质量", "unit": "kg"}
  ],
  "sub_questions": [
    {
      "id": "Q1",
      "question": "第一问",
      "goal": "求速度 v",
      "device_scene_needed": true,
      "variable_annotations": ["m", "h", "v"],
      "given_conditions": ["斜面光滑", "由静止释放"],
      "method_choice": {"method": "energy", "reason": "先修概念为机械能守恒，先求碰撞前速度"},
      "derivation_steps": [
        {"type": "reasoning", "content": "机械能守恒：mgh = 1/2 mv^2"},
        {"type": "equation", "content": "v = sqrt(2gh)"},
        {"type": "compute", "content": "代入 g=10, h=0.8，得 v=4 m/s"}
      ],
      "result": {"expression": "v=4", "unit": "m/s"},
      "sanity_checks": ["单位为 m/s", "h 增大时 v 增大，趋势合理"],
      "transition": "将该速度作为碰撞前速度进入下一问",
      "scene_packets": [
        {"content_items": ["diagram", "goal", "knowns"], "primary_item": "diagram"},
        {"content_items": ["principle", "core_equation", "substitute_compute"], "primary_item": "core_equation"},
        {"content_items": ["conclusion", "check_sanity", "transition"], "primary_item": "conclusion"}
      ]
    }
  ]
}
