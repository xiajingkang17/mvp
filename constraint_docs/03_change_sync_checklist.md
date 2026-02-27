# 约束改动同步清单

每次修改约束（新增/修复/重构）时，按以下清单同步：

## 必改项

1. 约束实现代码  

- `render/composite/solver/`

1. 约束说明文档  

- `render/composite/solver/CONSTRAINTS.md`

1. 本目录待办/规则文档  

- `constraint_docs/02_llm_integration_todo.md`（若涉及 LLM 联动）  
- `constraint_docs/01_scope_and_usage.md`（若阶段目标变化）

1. 测试  

- `tests/test_composite_solver_static.py`  
- 必要时补场景测试：`render/composite/solver/test/`

## 验证建议

- 先跑约束单测：`pytest -q tests/test_composite_solver_static.py`
- 再跑全量测试：`pytest -q`

## 提交前自检

- 约束行为是否与文档一致。
- 新参数是否有默认值和边界说明。
- 圆弧场景是否显式处理 `contact_side`。
- 若使用 `auto_clearance`，是否验证了不同轨道类型默认值符合预期。
