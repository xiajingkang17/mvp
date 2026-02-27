# MVP（独立项目，Scene-first 多 LLM 分工）

这个 `MVP/` 目录被设计成可单独拎出去的项目：不依赖仓库其它模块。

目标：

- LLM 自由设计每一个 scene（不强制任何布局模板）
- 先保证“正确性 + 可运行”：生成 -> 渲染 -> 报错 -> 修复循环
- 最终只产出一个可直接运行的 `scene.py`（单一 Scene 类），渲染得到 `final.mp4`

## 目录结构

- `run_mvp.py`：一键编排入口（需求 -> scene 规划 -> scene 设计 -> 代码 -> 渲染 -> 修复）
- `pipeline/`：核心流水线代码（配置/LLM 调用/渲染封装等）
- `prompts/`：各 LLM 的 prompt（中文，按文件夹组织，支持 `bundle.md` 拼接）
  - `prompts/llm1_analyst/`
  - `prompts/llm2_scene_planner/`
  - `prompts/llm3_scene_designer/`
  - `prompts/llm4_codegen/`
  - `prompts/llm5_fixer/`
- `configs/llm.yaml`：LLM 配置（stage/mode 采样策略）
- `.env`：密钥与运行参数（不提交，参考 `.env.example`）
- `runs/`：每次运行产物（已在 `.gitignore` 忽略）

## 配置说明

### 1) `.env`（优先级最高）

复制模板：

```powershell
Copy-Item .env.example .env
```

至少需要：

- `ZHIPUAI_API_KEY=...`

### 2) `configs/llm.yaml`

用于配置不同角色的采样参数（例如 `analyst/scene_planner/...`），并提供默认模型等信息。

配置优先级：`.env` > `configs/llm.yaml` > 内置默认值（实现见 `pipeline/llm/zhipu.py`）。

## 安装依赖

```powershell
pip install -r requirements.txt
```

说明：

- `manim` 需要系统侧的额外依赖（FFmpeg、LaTeX 等），按你的环境安装即可。
- 如果只想先“生成代码不渲染”，可以用 `--no-render`，那就不依赖本机的 manim 安装是否完整。

## 运行

推荐在 `MVP/` 目录内运行：

```powershell
python run_mvp.py -r "用动画讲清楚勾股定理，并给一个简单例题"
```

也支持从父目录运行：

```powershell
python MVP/run_mvp.py -r "..."
```

运行结束后，你会在运行目录里得到 `scene.py`，也可以手动渲染：

```powershell
manim -ql <run_dir>/scene.py MainScene
```

默认情况下，`run_mvp.py` 会自动执行渲染并进入修复循环，直到成功或达到最大轮数。常用命令：

```powershell
python run_mvp.py -r "..." --max-fix-rounds 10 --quality l
```

## Case 测试（输入为 txt）

我们在 `cases/` 下放测试用例，每个 case 至少包含一个输入文件：

- `cases/<case_name>/problem.txt`：问题/需求输入（纯文本）

示例 case：`cases/demo_001/problem.txt`

一键跑完整流水线（从输入文件读需求）：

```powershell
python run_mvp.py --requirement-file cases/demo_001/problem.txt
```

如果你想先只生成代码、不渲染：

```powershell
python run_mvp.py --requirement-file cases/demo_001/problem.txt --no-render
```

当 `--requirement-file` 位于 `cases/<case_name>/` 下时，默认把产物写回该 case 目录（并按 `llm1/..llm5/`、`render/` 分文件夹）。
如果你想把产物落到其它目录，再显式指定 `--run-dir`。

## 分阶段运行（像原项目一样拆开 5 个 LLM）

在 `MVP/` 目录内执行：

```powershell
# LLM1：分析 + 前置探索（会自动创建 runs/<时间戳>_<slug>/）
python pipeline/run_llm1.py -r "用动画讲清楚勾股定理，并给一个简单例题"
```

说明：分阶段脚本（`run_llm1.py` ~ `run_llm4.py`）现在默认“再次运行即重新生成并覆盖同名产物”，不再因为文件已存在而跳过。
旧参数 `--force` 仅为兼容保留，已无实际作用。

然后把上一步输出的 `runs/<...>` 作为 `--run-dir` 继续：

```powershell
# LLM2：scene 拆分规划
python pipeline/run_llm2.py --run-dir runs/<...>

# LLM3：逐 scene 设计（分镜级，聚合到一个 JSON）
python pipeline/run_llm3.py --run-dir runs/<...>

# LLM4：整合成单文件 scene.py，并自动执行“渲染 -> 报错 -> LLM5 修复 -> 重渲染”循环
python pipeline/run_llm4.py --run-dir runs/<...> --max-fix-rounds 10 --quality l
```

如果你只想生成 `scene.py` 不渲染：

```powershell
python pipeline/run_llm4.py --run-dir runs/<...> --no-render
```

`LLM5` 相关脚本现在作为“手动兜底工具”（可选）：

```powershell
# 手动触发 LLM5（不依赖 stderr，做一次预审查/预修复）
python pipeline/run_llm5_review.py --run-dir runs/<...>

# 给定 stderr（或 stderr 文件）手动触发 LLM5 修复
python pipeline/run_llm5.py --run-dir runs/<...> --stderr-file <path-to-stderr.txt>
```

按 case 输入文件分阶段运行（产物固定落在 case 目录）：

```powershell
python pipeline/run_llm1.py --requirement-file cases/demo_001/problem.txt --run-dir cases/demo_001
python pipeline/run_llm2.py --run-dir cases/demo_001
python pipeline/run_llm3.py --run-dir cases/demo_001
python pipeline/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
```

只跑某一个 scene：

```powershell
python pipeline/run_llm3.py --run-dir runs/<...> --scene-id scene_02
python pipeline/run_llm4.py --run-dir runs/<...> --scene-id scene_02 --max-fix-rounds 10
```

## 输出产物

每次运行会落在某个运行目录（默认 `runs/<时间戳>_<slug>/`；若 requirement-file 在 `cases/` 下则默认回写到 case 目录）。常见文件：

- `requirement.txt`：原始需求
- `llm1/stage1_analyst.json`：分析与前置探索输出
- `llm2/stage2_scene_plan.json`：scene 列表（含 `scene_id/class_name/duration_s`）
- `llm3/stage3_scene_designs.json`：所有 scene 的设计稿（聚合）
- `llm3/stage3_<scene_id>_raw.txt`：某个 scene 的原始设计输出（排查用）
- `llm4/scene.py`：LLM4 产出的单文件 Manim 代码（默认类名 `MainScene`）
- `scene.py`：导出一份到运行目录根部（便于直接运行）
- `llm5/fix_raw_*.txt`：修复轮次的原始输出（用于排查）
- `render/render_stderr_*.txt`：渲染错误日志（修复循环输入）
- `render/media/**/MainScene.mp4`：manim 的渲染产物
- `render/final.mp4`：从 manim 产物复制一份到 render 目录
- `final.mp4`：再导出一份到运行目录根部（方便取用）

## 可调参数

- `--max-fix-rounds`：渲染失败时的最大修复轮数（默认 5）
- `--quality`：渲染质量（默认 `l`，更快；可选 `m/h`）
- `--render-timeout-s`：单次渲染任务超时秒数（默认 300）
- `--no-render`：只生成代码，不执行 manim 渲染（便于先调 prompt）

## 常见问题

- 报错 `缺少 Zhipu API key`：
  - 检查 `MVP/.env` 是否有 `ZHIPUAI_API_KEY=...`
- 报错 `找不到 manim 命令`：
  - 先确认已安装 manim，并且 `manim` 已加入 PATH（或先激活你的虚拟环境再运行）
