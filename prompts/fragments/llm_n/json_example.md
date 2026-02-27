# 形状示例（仅示例）

{
  "analysis": {
    "target_concept": "完全非弹性碰撞中的能量与动量综合计算",
    "narrative_goal": "从先修概念逐步搭建到碰撞综合求解",
    "audience_level": "intermediate"
  },
  "global_arc": "先建立能量路径，再进入动量碰撞，最后回到能量损失解释。",
  "ordered_concepts": [
    "重力势能",
    "速度与动能",
    "动量守恒",
    "完全非弹性碰撞中的能量与动量综合计算"
  ],
  "segments": [
    {
      "id": "N1",
      "concept_ref": "重力势能",
      "sub_question_id": "Q1",
      "title": "势能到动能的桥梁",
      "narration": "先展示高度差，再引出 mgh 与动能关系，作为碰撞前速度求解的起点。",
      "visual_intent": "图像聚焦斜面高度与底端速度箭头。",
      "key_equations": ["mgh=1/2mv^2"],
      "scene_focus": "core_equation",
      "transition_hook": "得到底端速度后，转入碰撞动量分析。",
      "duration_hint_s": 16
    }
  ],
  "style_guide": {
    "tone": "teacher_clear_precise",
    "pacing": "steady_foundation_to_target",
    "color_intent": "equation_blue_result_gold",
    "transition_principles": ["same_symbol_persistence", "single_focus_per_segment"],
    "narration_rules": ["state_goal_then_method", "equation_before_substitution"]
  },
  "explanation": "该叙事蓝图用于约束后续场景生成与布局决策。"
}
