# Schema 目录说明

`schema/` 用于定义项目里的核心数据模型（主要是 Pydantic 模型）和对外 JSON Schema。

## 文件用途

- `schema/composite_graph_models.py`  
  定义 `CompositeGraph` 相关模型：`parts`、`tracks`、`constraints`、`motions`、`seed_pose` 等，并做基础引用校验（如 `part_id/track_id` 是否存在）。

- `schema/scene_plan_models.py`  
  定义场景规划主模型：`ScenePlan`、`SceneSpec`、`ObjectSpec`、`LayoutSpec`、`ActionSpec`、`PedagogyPlan` 等，供 LLM 输出草稿与渲染流水线之间对接。

- `schema/teaching_plan_models.py`  
  定义教学规划模型：分问计划、推导步骤、符号说明、结果结构等，用于“讲解结构化输出”这一层。

- `schema/scene_plan.schema.json`  
  `ScenePlan` 的 JSON Schema 导出文件，便于外部系统做静态校验或联调。

- `schema/__init__.py`  
  包初始化文件（当前无额外逻辑）。

## 边界约定

- `schema/` 只负责“数据结构合法性”和基础引用一致性。  
- 约束白名单、锚点词典、LLM 专用规则放在 `llm_constraints/`（业务规则层）。  
