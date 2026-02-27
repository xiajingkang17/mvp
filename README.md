# MVP (Manim Plan Renderer)

这个项目把 `scene_plan.json` 渲染成 Manim Community `0.19.1` 视频，并提供一条可选的 LLM 生产流水线。

## 快速开始

建议环境：Python 3.12。

安装依赖：

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

渲染一个现有方案：

```powershell
$env:SCENE_PLAN = "cases/demo_001/scene_plan.json"
python -m manim -pql render/plan_scene.py PlanScene
```

`pin_to_corner` 动作原语示例：

```powershell
$env:SCENE_PLAN = "cases/demo_title_pin/scene_plan.json"
python -m manim -pql render/plan_scene.py PlanScene
```

## LLM ???????

??????????

```powershell
python -m pipeline.run_full_case --case cases/demo_001
```

???????

1. `llm0` -> `concept_tree.json`
2. `llm1` -> `teaching_plan.json`
3. `llm_n` -> `narrative_plan.json`
4. `llm2` -> `scene_semantic.json`
5. `llm_codegen_pre` -> ?? `scene_semantic.json` ??? `scene_codegen.json` + `llm_codegen.py`???? plan?
6. `llm_draw` -> `scene_draw.json`
7. `build_draft` -> `scene_draft.json`
8. `llm3` -> `scene_layout.json`
9. `build_plan` -> `scene_plan.json`
10. `llm_codegen` -> ??????? `scene_plan.json` ? `CustomObject.params`
11. `validate` -> ???? `scene_plan.json`

??? `--from-step` / `--to-step` / `--skip` ???????

## ??????

```powershell
python -m pipeline.run_llm0 --case cases/demo_001
python -m pipeline.run_llm1 --case cases/demo_001
python -m pipeline.run_llm_n --case cases/demo_001
python -m pipeline.run_llm2 --case cases/demo_001
# ?????? scene_semantic ?? CustomObject ?????? scene_plan?
python -m pipeline.run_llm_codegen --case cases/demo_001 --targets-from semantic --skip-apply-plan
python -m pipeline.run_llm_draw --case cases/demo_001
python -m pipeline.build_draft --case cases/demo_001
python -m pipeline.run_llm3 --case cases/demo_001
python -m pipeline.build_plan --case cases/demo_001
# ??????? scene_plan ????? code_key/spec
python -m pipeline.run_llm_codegen --case cases/demo_001
python -m pipeline.validate_plan cases/demo_001/scene_plan.json
```

`llm_codegen` ?????????

- `--targets-from semantic`?? `scene_semantic.json` ?? `CustomObject` ?????? `llm2 -> llm_codegen_pre -> llm_draw`?
- `--targets-from plan`?????? `scene_plan.json` ???????? `code_key/spec` ? plan

?????????????

```powershell
python -m pipeline.validate_plan cases/demo_001/scene_plan.json --autofix --write
```
## CustomObject 与 llm_codegen

`CustomObject` 是顶层对象类型，用于承载 LLM 生成的局部 Manim 代码。

`CustomObject.params` 关键字段：

- `code_key`: 对应 `llm_codegen.py` 里的构建器键
- `spec`: 构建/更新参数对象
- `code_file`: 代码文件路径，默认取 case 目录下 `llm_codegen.py`
- `motion_span_s`: 连续运动时长（秒，可选）

运行时由 `components/common/custom_object.py` 动态加载 `llm_codegen.py`，并使用：

- `BUILDERS[code_key](spec)` 构建 `Mobject`
- `UPDATERS[code_key](mobj, t, spec)` 做时间更新（可选）

如果 case 内没有 `CustomObject`，`llm_codegen` 会输出空 `scene_codegen.json` 并跳过实际代码生成。

## LLM 配置

- API Key 从 `.env` 读取，例如 `ZHIPUAI_API_KEY=...`
- 模型和各阶段采样参数见 `configs/llm.yaml`
- Prompt 组合系统在 `prompts/`（`bundles/` + `stages/` + `fragments/`）

## 动作原语

- 目录：`render/motions/`
- 示例：`pin_to_corner`（兼容别名 `title_pin`），实现见 `render/motions/pin_to_corner.py`

## 测试

```powershell
pytest -q
```

## 目录结构

- `schema/`: Pydantic 模型与 JSON 结构定义
- `layout/`: 布局模板与布局计算
- `components/`: 语义组件（含 `CompositeObject` / `CustomObject` / 物理组件）
- `render/`: `scene_plan.json` 执行与 Manim 渲染
- `pipeline/`: LLM 调用与各阶段构建脚本
- `prompts/`: 分阶段 Prompt 资源
- `cases/`: 输入题目、阶段产物与最终方案
