# Manim 教育视频多智能体流水线

根据学生需求自动生成、渲染、评测并迭代改进 Manim 教学视频的流水线。当前仓库支持一轮「生成 -> 渲染 -> 评测 -> 改进」循环，并在最终视频没有音轨时自动补一版 TTS 旁白。

## 功能概览

- 教学编排 Agent：先把题目整理成授课结构，明确导入、误区、分步讲解、总结与迁移问题。
- 代码生成：使用大模型生成 Manim 场景代码，支持中文、公式、字幕与讲解节奏。
- 渲染与修复：调用 Manim 渲染；若失败，会把报错交给模型修复并重试一次。
- 评测：结合 CV 指标与 VLM 语义判断，对视频做结构化打分。
- 改进：若首轮未通过，会结合评测结果和关键帧截图做第二轮改进。
- TTS 兜底：如果最终视频没有内嵌音轨，会额外生成 `final_with_audio.mp4`。

## 环境要求

- Python 3.10+
- [Manim Community](https://www.manim.community/)（渲染）
- FFmpeg（音视频合成；推荐安装）
- Tesseract（OCR 评测可选）

安装 Manim 与系统依赖请参考 [Manim 官方文档](https://docs.manim.community/en/stable/installation.html)。

## 安装

```bash
cd manim-edu-agent
pip install -r requirements.txt
```

项目不会自动提供 `.env.example`，请在仓库根目录手动创建 `.env`。

## 配置

启动时会自动加载根目录下的 `.env`。

最少需要：

```dotenv
OPENAI_API_KEY=your-api-key
```

可选配置：

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.example.com/v1
OPENAI_MODEL=gpt-4o
```

说明：

- `agent_pipeline` 默认模型是 `gpt-4o`。
- `eval_pipeline` 默认模型是 `gpt-5.4`。
- 如果显式设置了 `OPENAI_MODEL`，两条管线都会优先使用这个值。
- 如果使用 OpenAI 兼容服务，可通过 `OPENAI_BASE_URL` 覆盖默认地址。

## 使用

### 生成完整视频

从项目根目录运行：

```bash
python -m agent_pipeline "用动画讲解一下质量为 m 的小球用长为 L 的轻绳悬挂于 O 点，在竖直平面内做圆周运动。小球经过最高点时，绳子拉力恰好为零。重力加速度为 g，下列说法正确的是（） A. 小球在最高点的速度大小为 √gL B. 小球在最低点的速度大小为 2√gL C. 小球从最高点到最低点，重力做功为 mgL D. 小球在最低点时，绳子的拉力大小为 5mg"
```

例如：

```bash
python -m agent_pipeline "用供需曲线动画解释通货膨胀下供不应求如何导致价格上涨"
```

带图片输入：

```bash
python -m agent_pipeline "用动画推导一下椭圆的高中常见的二级结论" --image path/to/problem.png
```

只提供图片也可以：

```bash
python -m agent_pipeline --image path/to/problem.png
```

自定义输出目录：

```bash
python -m agent_pipeline "讲解洛必达法则" --run-dir runs/lhopital_demo
```

### 输出目录

默认输出到 `runs/YYYYMMDD_HHMMSS/`，通常包含：

- `request.txt`：本次请求文本。
- `request_image.*`：如果传入了图片，会复制一份到运行目录。
- `teaching_plan.json`：教学编排结果。
- `round1/`、`round2/`：每轮的代码、渲染日志、视频与评测结果。
- `summary.json`：两轮汇总、最终选中视频路径和最终分数。

常见最终产物：

- `round*/.../*.mp4`：每轮渲染出来的视频。
- `summary.json` 中的 `final_video`：最终选中的视频。
- `summary.json` 中的 `final_video_with_audio`：如果触发了 TTS 兜底，会额外生成这一版。

## 仅运行评测管道

若只想对已有视频做 CV + VLM 评测：

```bash
python -m eval_pipeline path/to/video.mp4 -o path/to/eval_output
```

CV-only 模式：

```bash
python -m eval_pipeline path/to/video.mp4 --skip-vlm
```

更多常用参数：

- `-o, --output-dir`：评测输出目录。
- `--skip-vlm`：跳过 VLM，只做 CV 评测。
- `--api-key` / `--base-url` / `--model`：覆盖评测阶段的模型配置。
- `--max-vlm-segments`：限制送去 VLM 的片段数。
- `--vlm-all`：把所有片段都送给 VLM。

完整参数见：

```bash
python -m eval_pipeline --help
```

## HTTP API

可启动一个简单 API 服务，让外部只提交文本需求：

```bash
python app.py
```

默认监听 `http://0.0.0.0:8000`，可通过环境变量覆盖：

```bash
set APP_HOST=127.0.0.1
set APP_PORT=8080
python app.py
```

服务根路径会返回接口说明：

```bash
curl http://127.0.0.1:8000/
```

### 1. 提交任务

```bash
curl -X POST http://127.0.0.1:8000/jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"request\":\"用动画讲解牛顿迭代法为什么会收敛\"}"
```

说明：

- 当前 `POST /jobs` 只接受 JSON 文本请求。
- 目前不支持通过 API 上传图片。

返回里会包含：

- `job_id`：任务 ID。
- `status_url`：状态查询接口。
- `video_url`：生成完成后的视频下载接口。

### 2. 查询任务状态

```bash
curl http://127.0.0.1:8000/jobs/<job_id>
```

状态可能为：

- `queued`
- `running`
- `completed`
- `failed`

### 3. 获取视频

```bash
curl -L http://127.0.0.1:8000/videos/<job_id> --output lesson.mp4
```

接口会优先返回带音频版本；若没有带音频版本，则返回 `final_video`。

## 项目结构

```text
manim-edu-agent/
├── agent_pipeline/
│   ├── __main__.py          # 支持 python -m agent_pipeline
│   ├── main.py              # 主入口与生成-评测循环
│   ├── teaching_planner.py  # 教学编排 Agent
│   ├── code_gen.py          # 代码生成 / 修复 / 改进
│   ├── renderer.py          # Manim 渲染与字幕/TTS辅助
│   ├── evaluator.py         # 调用 eval_pipeline 做视频评测
│   └── tts.py               # edge-tts 与 ffmpeg 音视频合成
├── colortest/
│   ├── __init__.py
│   ├── ai4learning_theme.py # 主题颜色、背景与场景基类
│   ├── narrated_scene.py    # 字幕与旁白辅助基类
│   └── pic.png              # 默认背景资源
├── eval_pipeline/
│   ├── __main__.py          # 支持 python -m eval_pipeline
│   ├── run.py               # 评测主入口
│   ├── config.py
│   ├── cv_features.py
│   ├── vlm_judge.py
│   └── fusion.py
├── app.py                   # 简单 HTTP API 服务
├── runs/                    # 每次运行的输出目录
├── requirements.txt
└── README.md
```

## 许可证

按需自定。
