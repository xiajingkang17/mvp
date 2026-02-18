# run_llm2 瘦身待办（后续）

## 背景

当前 `pipeline/run_llm2.py` 中仍包含较多与约束规则、组件筛选、提示词拼接相关的辅助函数。  
这些逻辑与 `llm_constraints/` 目录职责重叠，后续应做职责收敛。

## 目标

将“规则资产与规则逻辑”集中到 `llm_constraints/`，让 `run_llm2.py` 主要负责流程编排。

## 计划拆分

1. 迁移规则读取与缓存  

- 从 `run_llm2.py` 迁出 `constraints_whitelist / anchors_dictionary / components_catalog` 的加载逻辑  
- 在 `llm_constraints/` 统一提供加载接口

1. 迁移分类与筛选逻辑  

- 将领域分类、组件筛选、约束注入数据构造迁入 `llm_constraints/selector.py`（或同类模块）

1. 迁移提示词片段构造  

- 将约束白名单、组件清单、锚点词典相关的 prompt 片段构造迁入 `llm_constraints/prompt_bundle.py`

1. 缩减 run_llm2 主文件职责  

- `run_llm2.py` 保留：读取输入、调用 LLM、继续输出、写文件、触发校验  
- 规则相关细节改为调用 `llm_constraints` 的公开函数

## 验收标准

- `run_llm2.py` 中与规则/筛选相关的私有辅助函数显著减少  
- `llm_constraints/` 成为规则资产与规则逻辑唯一入口  
- 现有测试（尤其 `tests/test_llm2_draft_validation.py`）保持通过
