# mvp (Manim plan renderer)

这是一个把 `scene_plan.json`（基于 slot/layout 的可执行场景计划）渲染成 Manim Community `0.19.1` 视频的项目。
同时也包含一条可选的 LLM 流水线：从题目/讲解草稿逐步生成 `scene_plan.json`。

## 快速开始

环境：建议 Python 3.12。

安装依赖：

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

渲染（从环境变量读取计划文件）：

```powershell
$env:SCENE_PLAN = "cases/demo_001/scene_plan.json"
python -m manim -pql render/plan_scene.py PlanScene
```

动作原语 demo（把任意 object “居中出现 → 钉到角落”）：

```powershell
$env:SCENE_PLAN = "cases/demo_title_pin/scene_plan.json"
python -m manim -pql render/plan_scene.py PlanScene
```

## LLM 流水线（可选）

按 case 目录运行（例：`cases/demo_001/`）：

```powershell
python -m pipeline.run_llm1 --case cases/demo_001
python -m pipeline.run_llm2 --case cases/demo_001
python -m pipeline.run_llm3 --case cases/demo_001
python -m pipeline.build_plan --case cases/demo_001
```

LLM Key：项目读取 `.env`（例如 `ZHIPUAI_API_KEY=...`）；模型与采样参数在 `configs/llm.yaml`。

计划校验（可自动修复并写回）：

```powershell
python -m pipeline.validate_plan cases/demo_001/scene_plan.json
python -m pipeline.validate_plan cases/demo_001/scene_plan.json --autofix --write
```

## 动作原语（Motion Primitives）

为了减少“模板堆砌感”，建议把常用小动画做成可复用原语，让 LLM 只输出“选哪个原语 + 参数”，由渲染层稳定落地。

- 原语目录：`render/motions/`
- 例：`pin_to_corner`（兼容旧别名 `title_pin`），实现见 `render/motions/pin_to_corner.py`

## 测试

```powershell
pytest -q
```

## 目录结构

- `schema/`：Pydantic 数据模型 + JSON Schema
- `layout/`：slot 模板 + 布局引擎（不依赖 Manim）
- `components/`：语义组件（TextBlock / BulletPanel / Formula / CompositeObject / 物理组件等）
- `render/`：解释执行 `scene_plan.json` 的 Manim runner（`render/plan_scene.py`）
- `render/motions/`：动作原语库（供 `action.anim` 调用）
- `pipeline/`：LLM 调用 + 构建/校验 scene plan
- `cases/`：样例与产物（输入、LLM 输出、最终 plan、资源等）
