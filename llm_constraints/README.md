# llm_constraints 目录说明

用于集中管理 LLM 与程序共享的约束规范。

## 目录

- `specs/`：机器规则真源（白名单、锚点字典、组件目录）
- `protocols/`：给 LLM 的协议文档
- `patterns/`：可复用 JSON 模式
- `tools/`：一致性/覆盖率检查脚本
- `constraints_spec.py`：读取 `specs/constraints_whitelist.json` 并做参数校验

## 说明

- 当前约束体系不包含 `align_angle/align_axis`。
- 轨道骨架连接建议使用 `attach`（可配 `rigid=true`）。
