# Manim4Teach

`Manim4Teach` 是当前使用中的两级 Agent 管线目录。
当前实现为**自包含命名空间**，不依赖 `MVP.pipeline.*` 导入。

## 目标

- 只保留两个主阶段：

1. LLM1：`analysis_packet` 生产器（双模式分流）
2. LLM2：围绕 `scene.py` 的生成、渲染修复、视觉修稿闭环

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
- `prompts/llm2_director_draft/`：二级首稿生成提示词
- `prompts/llm2_runtime_fix/`：二级运行修复提示词，只负责“让它能渲染”
- `prompts/llm2_visual_fix/`：二级视觉修稿提示词，只负责“让图和动画表达变对、变清楚”
- `prompts/review_rubrics/`：教学图评审规则，`common + math/physics`
- `schema/analysis_packet.schema.json`：一级输出 JSON Schema（定死）
- `pipeline/core/`：公共能力（env/config/llm/json）
- `pipeline/stage1/`：一级分析与 schema 归一化
- `pipeline/stage2/`：二级生成、渲染、评审、修稿循环
- `pipeline/runners/`：可执行入口脚本

## LLM2 当前模式

LLM2 当前不是单次“导演修稿”，而是拆成 3 个子能力：

1. `director_draft`
   基于 `analysis_packet` 先生成第一版可看的 `scene.py`
2. `runtime_fix`
   只处理预览失败、语法/API/对象生命周期等运行问题，目标是恢复可渲染
3. `visual_fix`
   只处理教学图、空间关系、过程动画、主体突出等视觉表达问题

配套还有两层评审：

1. `review_rules`
   本地规则检查，优先卡住 `preview_failed`
2. `review_vlm`
   基于关键帧做视觉评审，决定是否进入 `visual_fix`

默认回路是：

1. `director_draft`
2. `preview render`
3. 若渲染失败，进入 `runtime_fix`
4. `review_rules` + `review_vlm`
5. 若视觉不过关，进入 `visual_fix`
6. 继续下一轮，直到通过或达到 `max_rounds`

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
- `final/runtime_fix.json`
- `final/vlm_review.json`
- `final/preview.mp4`（若未 `--skip-preview`）
- `final/meta.json`（轮次、停止原因、runtime/rule/VLM 关键摘要）

说明：

- 当低清预览失败时，LLM2 会先进入专门的 `runtime_fix` 小循环，优先修复编译/运行错误。
- 当预览可用后，才进入规则评审与 VLM 视觉评审。
- `visual_fix` 会使用 `review_rubrics/` 中的 `common` 规则和按学科选择的 `math` / `physics` 规则。

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
