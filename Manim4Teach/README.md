# Manim4Teach

`Manim4Teach` 是新的两级 Agent 管线实验目录。
当前实现为**自包含命名空间**，不依赖 `MVP.pipeline.*` 导入。

## 目标

- 只保留两个 LLM：

1. LLM1：`analysis_packet` 生产器（双模式分流）
2. LLM2：统一的教学视频创作与代码生成器（后续接入）

## LLM1 设计原则

- 不再同时输出“完整教学稿 + 视觉细节 + 分镜细节”。
- 当前版本只保留最小输出：

1. 解题类只输出完整解题过程
2. 概念类只输出知识树

- 强制双模式：

1. `mode = "problem"`：解题类
2. `mode = "concept"`：概念讲解类

## 目录说明

- `prompts/llm1_analysis_packet/`：一级提示词（中文）
- `prompts/llm2_director_draft/`：二级首稿提示词
- `prompts/llm2_director_revise/`：二级修稿提示词
- `schema/analysis_packet.schema.json`：一级输出 JSON Schema（定死）
- `pipeline/core/`：公共能力（env/config/llm/json）
- `pipeline/stage1/`：一级分析与 schema 归一化
- `pipeline/stage2/`：二级导演循环模块
- `pipeline/runners/`：可执行入口脚本

## 环境变量

- 固定从 `Manim4Teach/.env` 加载。
- 已创建模板文件：`Manim4Teach/.env`。
- 使用 Claude 时请填写：`ANTHROPIC_AUTH_TOKEN`（或 `ANTHROPIC_API_KEY`）。
- 启用视觉评审可设置：`M4T_ENABLE_VLM=1`（可选 `M4T_VLM_MAX_IMAGES=3` 控制关键帧数量）。

## 快速运行

在仓库根目录执行：

```powershell
python Manim4Teach/pipeline/runners/run_stage1_analysis_packet.py --requirement "已知 x+y=1，求 x^2+y^2 最小值"
```

产物默认写入：

- `Manim4Teach/runs/<timestamp>_<slug>/llm1/stage1_analysis_packet.json`
- `Manim4Teach/runs/<timestamp>_<slug>/llm1/stage1_analysis_packet_raw.txt`

## 二级循环运行

```powershell
python Manim4Teach/pipeline/runners/run_llm2_loop.py `
  --analysis-packet "Manim4Teach/runs/<你的run>/llm1/stage1_analysis_packet.json" `
  --requirement "你的讲解需求" `
  --max-rounds 3
```

二级最终产物（默认极简）：

- `final/scene.py`
- `final/vlm_review.json`
- `final/preview.mp4`（若未 `--skip-preview`）
- `final/meta.json`（轮次、停止原因、规则/VLM 关键摘要）

## Case 测试（推荐）

1. 在 `Manim4Teach/cases/case_001/question.txt` 写入题目或讲解需求。
   支持图片路径（`图片: ./x.png` 或 `![img](./x.png)`，仅用于 LLM1 分析）。
2. 运行：

```powershell
python Manim4Teach/pipeline/runners/run_case.py --case-dir Manim4Teach/cases/case_001
```

可选参数：

- `--max-rounds 3`
- `--skip-preview`
