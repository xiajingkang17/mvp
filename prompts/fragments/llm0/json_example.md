# JSON 结构示例（仅示例形状）


{
  "analysis": {
    "core_concept": "完全非弹性碰撞",
    "domain": "physics/mechanics",
    "level": "intermediate",
    "goal": "理解碰后共速与机械能损失"
  },
  "root_id": "n0",
  "nodes": [
    {"id": "n0", "concept": "完全非弹性碰撞", "depth": 0, "is_foundation": false, "rationale": "目标概念"},
    {"id": "n1", "concept": "动量守恒", "depth": 1, "is_foundation": false, "rationale": "碰撞阶段核心守恒规律"},
    {"id": "n2", "concept": "速度与向量", "depth": 2, "is_foundation": true, "rationale": "基础量与方向描述"}
  ],
  "edges": [
    {"from_id": "n0", "to_id": "n1", "relation": "requires"},
    {"from_id": "n1", "to_id": "n2", "relation": "requires"}
  ],
  "ordered_concepts": [
    "速度与向量",
    "动量守恒",
    "完全非弹性碰撞"
  ],
  "explanation": "通过逆向先修分解，从基础概念逐层构建到目标概念。"
}
