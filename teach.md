# 测试流程（从题目到视频）

以下流程以 `cases/demo_001/` 为例，覆盖 **LLM 流水线 → 计划校验 → 渲染** 的完整链路。

---

## 0) 准备环境

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

---

## 1) 配置智谱 API Key

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填写：

```text
ZHIPUAI_API_KEY=你的Key
```

---

## 2) 准备题目文件

编辑或新建：

```
cases/demo_001/problem.md
```

示例内容（可替换为你自己的题目）：

```markdown
# 示例：一元一次方程

已知：\(2x + 3 = 11\)

求：\(x\)

提示：移项并化简。
```

---

## 3) 运行 LLM 流水线

按顺序执行：

```powershell
python -m pipeline.run_llm1 --case cases/demo_001
python -m pipeline.run_llm2 --case cases/demo_001
python -m pipeline.run_llm3 --case cases/demo_001
python -m pipeline.build_plan --case cases/demo_001
```

产物说明：

- `explanation.txt`：LLM1
- `scene_draft.json`：LLM2
- `scene_layout.json`：LLM3
- `scene_plan.json`：最终可执行计划

如果 LLM2/LLM3 报 “未找到 JSON 起始符号（{ 或 [）”，说明模型输出不是 JSON。此时请打开以下文件查看原始输出：

- `cases/demo_001/llm2_raw.txt`、`cases/demo_001/llm2_repair_raw.txt`
- `cases/demo_001/llm3_raw.txt`、`cases/demo_001/llm3_repair_raw.txt`

你也可以用 `--no-repair` 关闭二次修复（不推荐）：

```powershell
python -m pipeline.run_llm2 --case cases/demo_001 --no-repair
python -m pipeline.run_llm3 --case cases/demo_001 --no-repair
```

---

## 4) 校验与自动修复（可选但推荐）

```powershell
python -m pipeline.validate_plan cases/demo_001/scene_plan.json
python -m pipeline.validate_plan cases/demo_001/scene_plan.json --autofix --write
```

---

## 5) 渲染视频

```powershell
$env:SCENE_PLAN = "cases/demo_001/scene_plan.json"
manim -pql render/plan_scene.py PlanScene
```

如果没有 `manim` 命令：

```powershell
python -m manim -pql render/plan_scene.py PlanScene
```

---

## 6) 只看模板布局效果（可选）

```powershell
manim -pql examples/templates/preview_left3_right3.py PreviewLeft3Right3
```

---

## 7) 常见问题

1. **报 `No module named 'pydantic'`**

```powershell
python -m pip install -r requirements.txt
```

1. **Pylance 提示找不到 pytest**

```powershell
python -m pip install -r requirements-dev.txt
```
