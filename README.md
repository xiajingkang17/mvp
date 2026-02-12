# mvp_manim

从经过校验、基于插槽（slot）的 `scene_plan.json` 生成 Manim（0.19.1）视频。

## 环境要求

- Python 3.12（建议）
- Manim Community `0.19.1`

## 安装依赖

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## 配置环境变量（智谱）

1. 复制示例文件：

   ```powershell
   Copy-Item .env.example .env
   ```

1. 编辑 `.env`，至少填写：

   ```text
   ZHIPUAI_API_KEY=你的Key
   ```

默认模型/采样参数在 `configs/llm.yaml`，也可以用 `.env` 覆盖（见 `.env.example`）。

## 运行 LLM 流水线（可选）

对任意 `cases/<case_id>/`：

```powershell
python -m pipeline.run_llm1 --case cases/demo_001
python -m pipeline.run_llm2 --case cases/demo_001
python -m pipeline.run_llm3 --case cases/demo_001
python -m pipeline.build_plan --case cases/demo_001
```

说明：

- LLM1：`problem.md` → `explanation.txt`
- LLM2：`problem.md + explanation.txt` → `scene_draft.json`
- LLM3：`scene_draft.json` → `scene_layout.json`
- Build：`scene_draft.json + scene_layout.json` → `scene_plan.json`

如果 LLM2/LLM3 输出不是严格 JSON（常见报错：未找到 `{`/`[`），脚本会把原始输出写入：

- `cases/<case_id>/llm2_raw.txt`、`cases/<case_id>/llm2_repair_raw.txt`
- `cases/<case_id>/llm3_raw.txt`、`cases/<case_id>/llm3_repair_raw.txt`

可用 `--no-repair` 关闭二次修复（不推荐）：

```powershell
python -m pipeline.run_llm2 --case cases/demo_001 --no-repair
python -m pipeline.run_llm3 --case cases/demo_001 --no-repair
```

布局说明：

- LLM2 需在对象 `style` 中给出 `size_level`（S/M/L/XL）
- LLM3 仅可在 `layout.params` 中给出 `slot_scales`（按 slot 单独缩放宽高）
- 渲染时采用“LLM 初稿 + 真实测量微调”混合策略（默认±10%微调，最小 slot 宽高 10% 屏幕）

## 校验（可自动修复）

```powershell
python -m pipeline.validate_plan cases/demo_001/scene_plan.json
python -m pipeline.validate_plan cases/demo_001/scene_plan.json --autofix --write
```

## 渲染

Manim Runner 会从环境变量 `$env:SCENE_PLAN` 读取计划路径：

```powershell
$env:SCENE_PLAN = "cases/demo_001/scene_plan.json"
manim -pql render/plan_scene.py PlanScene
```

如果你的环境没有 `manim` 命令，也可以用：

```powershell
python -m manim -pql render/plan_scene.py PlanScene
```

## 测试

```powershell
pytest -q
```

## 目录结构

- `configs/`：全局配置 + 允许的枚举 + LLM 配置
- `schema/`：Pydantic 数据模型 + JSON Schema
- `layout/`：slot 模板 + 布局引擎（不依赖 Manim）
- `components/`：语义组件（TextBlock / BulletPanel / Formula ...）
- `render/`：解释执行 `scene_plan.json` 的 Manim Runner
- `pipeline/`：校验 + LLM 调用 + 构建计划
- `cases/`：每题产物（输入、LLM 输出、最终计划、资源、输出）

