## 输出结构（必须严格遵守）

### 1) problem 模式（只输出结构化 problem_solving）

```json
{
  "mode": "problem",
  "problem_solving": {
    "is_problem_video": true,
    "problem_statement": "题目原文",
    "known_conditions": [
      "条件1",
      "条件2"
    ],
    "target_question": "要求什么",
    "full_solution_steps": [
      {
        "step": 1,
        "goal": "本步目标",
        "reasoning": "为什么这样做",
        "equations": [
          "公式1",
          "公式2"
        ],
        "result": "本步得到的结论"
      }
    ],
    "final_answer": "最终答案",
    "answer_check": [
      "校验1"
    ]
  }
}
```

### 2) concept 模式（只输出知识树）

```json
{
  "mode": "concept",
  "knowledge_tree": {
    "target_concept": "...",
    "nodes": [
      {
        "node_id": "target",
        "concept": "目标概念",
        "type": "target"
      },
      {
        "node_id": "p1",
        "concept": "前置概念1",
        "type": "prerequisite"
      }
    ],
    "edges": [
      {
        "from": "p1",
        "to": "target",
        "relation": "prerequisite"
      }
    ]
  }
}
```

## 硬约束

1. `mode` 只能是 `"problem"` 或 `"concept"`。
2. `problem` 模式只允许 `mode + problem_solving` 两个顶层字段。
3. `concept` 模式只允许 `mode + knowledge_tree` 两个顶层字段。
4. `problem_solving` 必须包含且只包含：`is_problem_video/problem_statement/known_conditions/target_question/full_solution_steps/final_answer/answer_check`。
5. `problem` 模式下 `is_problem_video` 必须为 `true`。
6. `known_conditions`、`full_solution_steps`、`answer_check` 至少 1 项。
7. `full_solution_steps[*].equations` 至少 1 项。
8. 所有字符串字段必须非空。
9. `knowledge_tree.nodes` 至少 2 条（含目标节点与至少一个前置节点）。
10. `knowledge_tree.edges` 至少 1 条。
