# MVP

`MVP/` 是一个独立的 `scene-first` 多 LLM Manim 生成项目。

目标：

- 先把视频拆成 scene，再逐 scene 设计和编码
- 先保证“正确 + 可运行”，再追求视觉质量
- 最终只产出一个可直接运行的 `scene.py`，渲染得到 `final.mp4`

## 当前工作流

### LLM1: analyst

职责：

- 理解题目和用户需求
- 给出教学目标、受众、知识前置
- 对题目类内容完成完整求解

产物：

- `llm1/stage1_analyst.json`

### LLM2: scene planner

职责：

- 只负责全片 scene 序列与题解教学流程规划
- 让每个 scene 自己就是工作流里的一个节点
- 定义每个 scene 的教学角色、目标、输入前提、输出结果与承接关系

当前只使用新字段：

- 顶层：
  - `video_title`
  - `opening_strategy`
  - `question_structure`
- `scenes[*]`：
  - `workflow_step`
  - `question_scope`
  - `scene_goal`
  - `entry_requirement`
  - `key_points`
  - `scene_outputs`
  - `handoff_to_next`
  - `layout_prompt`
  - `panels`
  - `beat_sequence`
  - `duration_s`

LLM2 不再负责：

- object 生命周期
- object 保留清单
- `carry_over`
- 平行的 `workflow_strategy / workflow_trace`

产物：

- `llm2/stage2_scene_plan.json`

### LLM3: scene designer

职责：

- 为单个 scene 做完整视觉设计
- 定义 scene 开场状态、step 级状态、scene 收场状态
- 保证叙事过渡自然，并且每个 scene 的对象生命周期在本幕内闭合

当前只使用新 schema：

- `scene_id`
- `class_name`
- `narration`
- `on_screen_text`
- `object_registry`
- `entry_state`
- `steps`
- `exit_state`
- `layout_contract`
- `motion_contract`

LLM3 现在默认一次生成整片 scenes 的设计稿，再按 scene 拆分落盘。
当前主链路采用“scene 对象完全独立”模式：每个 scene 都从空画面开始、在空画面结束，不做跨 scene object 继承。

其中：

- `entry_state.objects_on_screen` 固定为空集
- `steps[*].object_ops` 和 `steps[*].end_state_objects` 是 step 级显隐真源
- `exit_state.objects_on_screen` 固定为空集

LLM3 不再输出旧字段：

- `object_manifest`
- `lifecycle_contract`
- `scene_end_keep`
- `transition_in`
- `transition_out`
- `carry_over`

产物：

- `llm3/stage3_scene_designs.json`
- `llm3/stage3_scene_designs_raw.txt`
- `llm3/stage3_<scene_id>_raw.txt`
- `llm3/scenes/<scene_id>/design.json`

### LLM4: split codegen

LLM4 拆成 4 个子阶段：

- `LLM4A`: 共享 helper 与框架代码
- `LLM4B`: 单 scene 方法代码
- `LLM4C`: 单 scene motion 代码
- `LLM4D`: 最终装配单文件 `scene.py`

LLM4 现在严格按以下边界执行：

- scene 开头只看 `entry_state.objects_on_screen`
- step 级显隐只看 `steps[*].object_ops`
- scene 结束只看 `exit_state.objects_on_screen`

共享 helper 里：

- `reset_scene(...)` 用于空 entry scene
- `prepare_scene_entry(...)` 用于把当前对象收敛到精确 entry 集合
- `cleanup_step(...)` 用于 step 末清理
- `cleanup_scene(...)` 用于 scene 末保留精确 exit 集合

产物：

- `llm4/code_interface_contract.json`
- `llm4/framework/`
- `llm4/scenes/<scene_id>/`
- `llm4/motion/<scene_id>/`
- `llm4/assemble/`
- `llm4/scene.py`
- `<run_dir>/scene.py`

### LLM5: fixer

职责：

- 渲染失败后根据错误日志修复 `scene.py`

产物：

- `llm5/fix_raw_*.txt`
- 修复后的 `llm4/scene.py`

## 目录结构

- `run_mvp.py`: 一键运行入口
- `pipeline/`: 核心流程代码
- `prompts/`: 各阶段 prompt
- `configs/llm.yaml`: LLM 配置
- `.env`: API key 与环境配置
- `runs/`: 默认运行产物目录
- `cases/`: 测试 case

## 提示词结构

- `prompts/llm1_analyst/`
- `prompts/llm2_scene_planner/`
- `prompts/llm3_scene_designer/`
- `prompts/llm4a_framework_codegen/`
- `prompts/llm4b_scene_codegen/`
- `prompts/llm4c_motion_codegen/`
- `prompts/llm4d_assemble_codegen/`
- `prompts/llm4_codegen/`
- `prompts/llm5_fixer/`

`llm3_scene_designer` 当前 bundle 包含：

- `system.md`
- `layout_reference_templates.md`
- `../draw/physics/mechanics_motion_contract.md`
- `lifecycle.md`
- `layout_contract.md`
- `visual_spec.md`
- `narrative_guidelines.md`

## 安装

```powershell
pip install -r requirements.txt
```

至少需要：

- `ZHIPUAI_API_KEY=...`

```powershell
Copy-Item .env.example .env
```

## 一键运行

在 `MVP/` 目录内：

```powershell
python run_mvp.py -r "用动画讲清勾股定理，并给一个简单例题"
```

或从仓库根目录：

```powershell
python MVP/run_mvp.py -r "..."
```

只生成代码不渲染：

```powershell
python run_mvp.py -r "..." --no-render
```

手动渲染：

```powershell
manim -ql <run_dir>/scene.py MainScene
```

## Case 运行

示例输入：

- `cases/demo_001/problem.txt`

完整运行：

```powershell
python run_mvp.py --requirement-file cases/demo_001/problem.txt
```

只生成代码：

```powershell
python run_mvp.py --requirement-file cases/demo_001/problem.txt --no-render
```

如果 `--requirement-file` 位于 `cases/<case_name>/` 下，默认把产物写回该 case 目录。

## 分阶段运行

### 从头开始

```powershell
python pipeline/run_llm1.py -r "用动画讲清勾股定理，并给一个简单例题"
python pipeline/run_llm2.py --run-dir runs/<...>
python pipeline/run_llm3.py --run-dir runs/<...>
python pipeline/run_llm4.py --run-dir runs/<...> --max-fix-rounds 10 --quality l
```

### 对 case 分阶段运行

```powershell
python pipeline/run_llm1.py --requirement-file cases/demo_001/problem.txt --run-dir cases/demo_001
python pipeline/run_llm2.py --run-dir cases/demo_001
python pipeline/run_llm3.py --run-dir cases/demo_001
python pipeline/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
```

### 只重跑单个 scene

```powershell
python pipeline/run_llm3.py --run-dir runs/<...> --scene-id scene_02
python pipeline/run_llm4.py --run-dir runs/<...> --scene-id scene_02 --max-fix-rounds 10
```

## 重跑行为

当前脚本已经切到“重跑即清空下游产物”模式。

规则：

- `run_mvp.py` 重跑时，会清空当前 case/run 目录下所有阶段产物，然后重新生成
- `run_llm1.py` 会清空 `llm1` 以及所有下游目录
- `run_llm2.py` 会清空 `llm2` 以及所有下游目录
- `run_llm3.py` 全量运行时，会清空整个 `llm3` 以及下游 `llm4/llm5/render`
- `run_llm3.py --scene-id ...` 时，会删除该 scene 的旧 raw，并清空下游 `llm4/llm5/render`
- `run_llm4.py` 会清空 `llm4/llm5/render`，并删除根目录导出的 `scene.py` / `final.mp4`

这意味着：

- 不会继续在同一个 case 目录里累积旧的 stage3/stage4 文件
- 不会出现“这次运行混进上次的 llm4 片段”这种情况

## 主要产物

每次运行通常落在：

- `runs/<timestamp_slug>/`
- 或 `cases/<case_name>/`

常见文件：

- `requirement.txt`
- `llm1/stage1_analyst.json`
- `llm2/stage2_scene_plan.json`
- `llm3/stage3_scene_designs.json`
- `llm3/stage3_scene_designs_raw.txt`
- `llm3/stage3_<scene_id>_raw.txt`
- `llm3/scenes/<scene_id>/design.json`
- `llm4/code_interface_contract.json`
- `llm4/framework/`
- `llm4/scenes/<scene_id>/`
- `llm4/motion/<scene_id>/`
- `llm4/assemble/`
- `llm4/scene.py`
- `scene.py`
- `llm5/fix_raw_*.txt`
- `render/render_stdout_*.txt`
- `render/render_stderr_*.txt`
- `render/final.mp4`
- `final.mp4`

## 已废弃旧字段

主链路已经彻底移除以下旧字段：

- `carry_over`
- `transition_in`
- `transition_out`
- `object_manifest`
- `lifecycle_contract`
- `scene_end_keep`

如果某个 case 或历史产物里还出现这些字段，它们属于旧输出，不代表当前主链路 schema。

## 常用参数

- `--max-fix-rounds`: 最大修复轮数，默认 5
- `--quality`: 渲染质量，默认 `l`
- `--render-timeout-s`: 单次渲染超时秒数，默认 300
- `--no-render`: 只生成代码，不执行 Manim 渲染

## 常见问题

### 缺少 API key

检查：

- `MVP/.env` 是否包含 `ZHIPUAI_API_KEY=...`

### 找不到 `manim`

检查：

- 当前环境是否已安装 `manim`
- 是否已激活正确的虚拟环境
- `manim` 是否在 PATH 中
