# AI4Learning Manim 项目说明（不含 `Math-To-Manim`）

本文档说明当前仓库中 **Manim 生产流水线** 的结构与执行逻辑。  
范围明确排除：`Math-To-Manim/` 子目录。

## 1. 项目目标

本项目的目标是把一道题目从文本输入，经过多阶段 LLM 规划与结构化校验，最终渲染为 Manim 视频。

核心产物是 `cases/<case_id>/scene_plan.json`，由 `render/plan_scene.py` 执行。

## 2. 顶层目录结构（排除 `Math-To-Manim`）

```text
manim/
├─ cases/                      # 每个 case 的输入与阶段产物
├─ components/                 # 可渲染对象组件库（Text/Formula/Physics/Composite/Custom）
├─ configs/                    # app/enums/llm 配置
├─ constraint_docs/            # 约束相关的历史/规划文档
├─ examples/                   # 示例模板
├─ layout/                     # 布局模板与布局计算
├─ llm_constraints/            # LLM 与程序共享的约束规格与协议
├─ pipeline/                   # LLM 流水线与构建脚本
├─ prompts/                    # Prompt 资源（bundle/stage/fragment）
├─ render/                     # scene_plan 执行与 Manim 渲染
├─ schema/                     # Pydantic 数据模型与 JSON schema
├─ tests/                      # 现有测试
├─ README.md
├─ requirements.txt
└─ requirements-dev.txt
```

## 3. 关键子系统职责

### 3.1 `pipeline/`（生产流水线）

主入口：

- `pipeline/run_full_case.py`

分阶段脚本：

- `pipeline/run_llm0.py`：生成 `concept_tree.json`
- `pipeline/run_llm1.py`：生成 `teaching_plan.json`
- `pipeline/run_llm_n.py`：生成 `narrative_plan.json`
- `pipeline/run_llm2.py`：生成 `scene_semantic.json`
- `pipeline/run_llm_draw.py`：生成 `scene_draw.json`
- `pipeline/build_draft.py`：合并 semantic + draw -> `scene_draft.json`
- `pipeline/run_llm3.py`：生成 `scene_layout.json`
- `pipeline/build_plan.py`：合并 draft + layout -> `scene_plan.json`
- `pipeline/run_llm_codegen.py`：生成 `scene_codegen.json` + `llm_codegen.py`，并回填 `scene_plan.json` 的 `CustomObject.params`
- `pipeline/validate_plan.py`：最终结构与业务校验（支持 `--autofix --write`）

配套模块：

- `pipeline/prompting.py`：按 bundle 组装系统提示词
- `pipeline/llm/zhipu.py`：调用 Zhipu 接口
- `pipeline/llm_continuation.py`：JSON 截断续写
- `pipeline/json_utils.py`：从模型输出中提取 JSON
- `pipeline/config.py`：读取 `configs/*.yaml`

### 3.2 `schema/`（数据契约）

主要模型文件：

- `schema/concept_tree_models.py`
- `schema/teaching_plan_models.py`
- `schema/narrative_plan_models.py`
- `schema/scene_semantic_models.py`
- `schema/scene_draw_models.py`
- `schema/composite_graph_models.py`
- `schema/scene_plan_models.py`
- `schema/scene_codegen_models.py`

说明：

- 这些模型是各阶段 JSON 的“硬契约”。
- pipeline 各阶段会在落盘前进行 schema 校验。

### 3.3 `components/`（对象构建层）

关键目录：

- `components/common/`：`TextBlock`、`Formula`、`BulletPanel`、`CustomObject`
- `components/composite/`：`CompositeObject` 组装器
- `components/physics/`：物理组件与参数白名单

关键文件：

- `components/composite/object_component.py`：`CompositeObject` 内部求解与 motion 应用
- `components/common/custom_object.py`：动态加载 case 下 `llm_codegen.py`
- `components/physics/specs.py`：物理组件参数白名单

### 3.4 `render/`（执行与渲染层）

关键文件：

- `render/plan_scene.py`：读取 `SCENE_PLAN`，构建对象、布局、执行 actions、推进时间轴
- `render/registry.py`：对象类型到组件实现的映射
- `render/actions.py`：`play/wait` 动作执行引擎

`CompositeObject` 相关：

- `render/composite/motion.py`：`on_track/on_track_schedule/state_driver`
- `render/composite/physics_world.py`：`physics_world` 预计算与采样
- `render/composite/solver/`：约束求解

动作原语扩展：

- `render/motions/pin_to_corner.py`

### 3.5 `layout/`（版式系统）

关键文件：

- `layout/templates/`：布局模板工厂（`hero_side`、`grid_2x2` 等）
- `layout/engine.py`：slot -> 屏幕坐标映射
- `layout/refine_params.py`：布局参数精修
- `layout/params.py`：参数清洗

### 3.6 `prompts/`（提示词资源）

结构：

- `prompts/bundles/*.json`：每个 stage 的拼装清单
- `prompts/stages/<stage>/base_system.md`：基础系统提示
- `prompts/fragments/<stage>/*.md|*.json`：可复用片段
- `prompts/json_repair.md`：通用修复提示

组装机制：

- `compose_prompt(stage)` 按 `bundle -> base + always + conditional` 拼接。

### 3.7 `llm_constraints/`（约束规格层）

职责：

- 作为 LLM 与程序共享的“协议真源”。

关键文件：

- `llm_constraints/specs/anchors_dictionary.json`
- `llm_constraints/specs/components_catalog.json`
- `llm_constraints/specs/constraints_whitelist.json`
- `llm_constraints/constraints_spec.py`
- `llm_constraints/protocols/*.md`

## 4. 端到端流程（文件级）

标准顺序由 `pipeline/run_full_case.py` 固定：

1. `llm0`：`problem.md` -> `concept_tree.json`
2. `llm1`：`problem.md` + `concept_tree.json` -> `teaching_plan.json`
3. `llm_n`：`problem.md` + `concept_tree.json` + `teaching_plan.json` -> `narrative_plan.json`
4. `llm2`：`problem.md` + `teaching_plan.json` + `narrative_plan.json` -> `scene_semantic.json`
5. `llm_codegen_pre`：读取 `scene_semantic.json` 中 `CustomObject` 标记 -> 预生成 `scene_codegen.json` + `llm_codegen.py`（不回填 plan）
6. `llm_draw`：`problem.md` + `scene_semantic.json` (+ teaching/narrative) -> `scene_draw.json`
7. `build_draft`：`scene_semantic.json` + `scene_draw.json` -> `scene_draft.json`
8. `llm3`：`scene_draft.json` -> `scene_layout.json`
9. `build_plan`：`scene_draft.json` + `scene_layout.json` (+ `narrative_plan.json`) -> `scene_plan.json`
10. `llm_codegen`：读取 `scene_plan.json` 中 `CustomObject` -> 生成 `scene_codegen.json` + `llm_codegen.py`，并更新 `scene_plan.json`
11. `validate`：校验最终 `scene_plan.json`

## 5. 各阶段产物含义

- `scene_semantic.json`：场景语义与叙事，不含 `CompositeObject.graph`
- `scene_draw.json`：只给 `CompositeObject.graph`（parts/tracks/constraints/motions）
- `scene_draft.json`：semantic + draw 的合并中间态
- `scene_layout.json`：布局与动作编排（layout + actions + keep）
- `scene_plan.json`：最终渲染计划（objects + scenes）
- `scene_codegen.json`：需要代码生成的 `CustomObject` 清单
- `llm_codegen.py`：`CustomObject` 的构建器与更新器实现

## 6. 运行方式

### 6.1 一键跑全流程

```powershell
python -m pipeline.run_full_case --case cases/demo_001
```

### 6.2 手动逐步执行

```powershell
python -m pipeline.run_llm0 --case cases/demo_001
python -m pipeline.run_llm1 --case cases/demo_001
python -m pipeline.run_llm_n --case cases/demo_001
python -m pipeline.run_llm2 --case cases/demo_001
# 预阶段：先按 scene_semantic 生成 CustomObject 代码（不回填 scene_plan）
python -m pipeline.run_llm_codegen --case cases/demo_001 --targets-from semantic --skip-apply-plan
python -m pipeline.run_llm_draw --case cases/demo_001
python -m pipeline.build_draft --case cases/demo_001
python -m pipeline.run_llm3 --case cases/demo_001
python -m pipeline.build_plan --case cases/demo_001
# 正式回填：基于 scene_plan 生成并写回 code_key/spec
python -m pipeline.run_llm_codegen --case cases/demo_001
python -m pipeline.validate_plan cases/demo_001/scene_plan.json
```

### 6.3 最终渲染

```powershell
$env:SCENE_PLAN = "cases/demo_001/scene_plan.json"
python -m manim -pql render/plan_scene.py PlanScene
```

## 7. `CompositeObject` 与 `CustomObject` 的边界

### 7.1 `CompositeObject`

适合：

- 标准组件拼装
- 轨道/约束驱动运动
- 规则化可校验图形

内部 graph 支持的 motion 重点：

- `on_track`
- `on_track_schedule`
- `state_driver`
- `physics_world`（依赖 pymunk）

### 7.2 `CustomObject`

适合：

- 标准 DSL 难表达的特殊组件、复杂形变、特效
- 需要直接写 Manim 代码的场景

运行方式：

- `scene_plan.objects[...].params` 中包含 `code_key/spec/code_file`
- `components/common/custom_object.py` 从 case 下 `llm_codegen.py` 动态加载
- 通过 `BUILDERS[code_key]` 和可选 `UPDATERS[code_key]` 执行

## 8. 校验与修复机制

各 LLM 阶段通用机制：

- 第一次输出后先 parse + schema validate
- 失败后按 `json_repair.md` 进行 repair rounds
- 中间文件写入 case 目录，便于定位

常见调试文件：

- `llm*_raw.txt`
- `llm*_repair_raw*.txt`
- `llm*_validation_errors.txt`
- `llm*_system_prompt.txt`

最终校验：

- `pipeline/validate_plan.py` 除 schema 外，还检查约束参数、锚点合法性、布局、预算等

## 9. 配置系统

- `configs/app.yaml`：画布、安全边距、默认字体与字号、布局精修参数
- `configs/enums.yaml`：对象类型、布局类型、action op、动画枚举
- `configs/llm.yaml`：模型与 stage 级采样参数
- `.env`：API key 与可覆盖参数（如 `ZHIPUAI_API_KEY`）

## 10. `cases/<case_id>/` 建议视图

一个典型 case（例如 `cases/demo_001`）包含：

- 输入：`problem.md`
- 主链产物：`concept_tree.json`、`teaching_plan.json`、`narrative_plan.json`、`scene_semantic.json`、`scene_draw.json`、`scene_draft.json`、`scene_layout.json`、`scene_plan.json`
- codegen 产物：`scene_codegen.json`、`llm_codegen.py`
- 调试文件：`llm*_raw*.txt`、`llm*_validation_errors.txt`、`llm*_system_prompt.txt`

## 11. 当前状态与建议

当前架构是“标准 DSL + 自定义代码逃生口”：

- 标准 DSL 保证可校验与稳定执行
- `CustomObject` 覆盖非标准复杂需求

这意味着项目可以覆盖大量多样题目，但不承诺“仅靠固定 DSL 覆盖所有题型”。  
真正的可扩展性来自：`CustomObject + llm_codegen`。
