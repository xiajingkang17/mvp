# MVP

`MVP/` 是一个以 `scene-first` 为核心的多 LLM Manim 生成流水线。

当前目标：

- 先把视频规划成一组 scene
- 先设计 scene 内容和布局，再做代码生成
- 最终产出一个可直接运行的 `scene.py`
- 渲染得到 `final.mp4`，渲染失败时再由 `llm5` 修复

## 当前工作流

现在有两套独立 workflow，位于 [pipeline](/e:/AI4Learning-Backend/manim/MVP/pipeline) 下。

### 1. 全智谱 workflow

目录：

- [pipeline/zhipu_workflow](/e:/AI4Learning-Backend/manim/MVP/pipeline/zhipu_workflow)

Provider 映射：

- `llm1 = zhipu`
- `llm2 = zhipu`
- `llm3 = zhipu`
- `llm35 = zhipu`
- `llm4 = zhipu`
- `llm5 = zhipu`

常用命令：

```powershell
python pipeline/zhipu_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
python pipeline/zhipu_workflow/run_llm1.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm2.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm3.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm35.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
python pipeline/zhipu_workflow/run_llm5.py --run-dir cases/demo_001
```

### 2. 混合 workflow

目录：

- [pipeline/mixed_workflow](/e:/AI4Learning-Backend/manim/MVP/pipeline/mixed_workflow)

Provider 映射：

- `llm1 = anthropic`
- `llm2 = kimi`
- `llm3 = kimi`
- `llm35 = anthropic`
- `llm4 = anthropic`
- `llm5 = anthropic`

常用命令：

```powershell
python pipeline/mixed_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
python pipeline/mixed_workflow/run_llm1.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm2.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm3.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm35.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
python pipeline/mixed_workflow/run_llm5.py --run-dir cases/demo_001
```

## 共用 prompts

两套 workflow 共用同一套 prompt 目录：

- [prompts](/e:/AI4Learning-Backend/manim/MVP/prompts)

当前主要 prompt bundle：

- [llm1_analyst](/e:/AI4Learning-Backend/manim/MVP/prompts/llm1_analyst)
- [llm2_scene_planner](/e:/AI4Learning-Backend/manim/MVP/prompts/llm2_scene_planner)
- [llm3_scene_designer](/e:/AI4Learning-Backend/manim/MVP/prompts/llm3_scene_designer)
- [llm35_layout_designer](/e:/AI4Learning-Backend/manim/MVP/prompts/llm35_layout_designer)
- [llm4e_batch_codegen](/e:/AI4Learning-Backend/manim/MVP/prompts/llm4e_batch_codegen)
- [llm5_fixer](/e:/AI4Learning-Backend/manim/MVP/prompts/llm5_fixer)

## 各阶段职责

### LLM1: analyst

产物：

- `llm1/stage1_analysis.json`
- `llm1/stage1_problem_solving.json`
- `llm1/stage1_drawing_brief.json`

### LLM2: scene planner

产物：

- `llm2/stage2_scene_plan.json`

### LLM3: scene designer

职责：

- 设计 scene 内容
- 拆分 steps
- 定义对象语义
- 产出 motion contract 草案

产物：

- `llm3/stage3_scene_designs.json`
- `llm3/stage3_scene_designs_raw.txt`
- `llm3/scenes/<scene_id>/design.json`

### LLM3.5: layout designer

职责：

- 输出 `layout_prompt`
- 输出 `layout_contract`
- 规划 scene 级 zones
- 规划对象组布局
- 输出 `step_layouts`

产物：

- `llm35/stage35_scene_layouts.json`
- `llm35/stage35_scene_layouts_raw.txt`
- `llm35/scenes/<scene_id>/layout.json`

### LLM4E: batch codegen

当前 codegen 模式：

- framework 由程序从 [execution_helpers.py](/e:/AI4Learning-Backend/manim/MVP/prompts/llm4e_batch_codegen/execution_helpers.py) 直接复制
- 单次 LLM 调用生成整片所有 `scene_method` 和 `motion_method`
- 程序把结果拆到 `scenes/` 和 `motion/`
- 最终 `scene.py` 由程序装配

产物：

- `llm4_*/code_interface_contract.json`
- `llm4_*/batch/`
- `llm4_*/framework/`
- `llm4_*/scenes/<scene_id>/`
- `llm4_*/motion/<scene_id>/`
- `llm4_*/assemble/`
- `llm4_*/scene.py`
- `<run_dir>/scene.py`

### LLM5: fixer

当前 fixer 模式：

- 先渲染整份 `scene.py`
- 如果渲染失败，把整份代码和 render 日志一起交给 `llm5`
- `llm5` 返回整份修复后的代码，再覆盖原文件

产物：

- `llm5/fix_raw_*.txt`
- 修复后的 `scene.py`

## 输出目录

典型 case 目录：

- `cases/<case_name>/`

常见产物：

- `requirement.txt`
- `llm1/`
- `llm2/`
- `llm3/`
- `llm35/`
- `llm4_zhipu/` 或 `llm4_claude/` 或 `llm4_kimi/`
- `llm5/`
- `render/`
- `scene.py`
- `final.mp4`

## 配置

主要配置文件：

- [configs/llm.yaml](/e:/AI4Learning-Backend/manim/MVP/configs/llm.yaml)
- [`.env`](/e:/AI4Learning-Backend/manim/MVP/.env)

安装：

```powershell
pip install -r requirements.txt
```

根据你要跑的 workflow，至少需要对应 provider 的 key。

### 智谱

```env
ZHIPUAI_API_KEY=...
```

### Anthropic / Claude 代理

```env
ANTHROPIC_AUTH_TOKEN=...
ANTHROPIC_BASE_URL=https://ai.jiexi6.cn/
```

或者：

```env
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=https://ai.jiexi6.cn/
```

### Kimi / Moonshot

```env
KIMI_API_KEY=...
```

或者：

```env
MOONSHOT_API_KEY=...
```

可选 Kimi 配置：

```env
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-128k
```

## 推荐运行命令

### 全智谱

```powershell
python pipeline/zhipu_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
```

### 混合 workflow

```powershell
python pipeline/mixed_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
```

### 带修复循环的渲染

```powershell
python pipeline/zhipu_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
python pipeline/mixed_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
```

## 说明

- 旧的根目录 workflow 入口脚本已经移除
- prompts 继续共用，workflow 编排逻辑已经拆开
- `llm4` 现在走程序化 framework copy 和程序化最终装配
- `llm4e` 下的组件参考已经支持动态注入
