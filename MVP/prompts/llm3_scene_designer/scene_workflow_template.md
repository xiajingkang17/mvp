# 单幕工作流细化模板（LLM3 参考）

你的职责不是重新规划整题，而是把 LLM2 已经规划好的单个 scene，细化成可直接供 LLM4 转代码的 JSON 设计稿。

换句话说：

- LLM2 决定“这幕为什么存在、处于整题 workflow 的哪一步”
- LLM3 决定“这幕开场先给观众看到什么、信息如何分区、按什么 step 推进、哪些信息必须稳定上屏”

## 总定位

把当前 scene 当成“单幕扩写任务”，而不是“重新设计整题讲法”。

优先级顺序：

1. 服从当前 scene 的 `workflow_step`
2. 服从当前 scene 的 `question_scope`
3. 服从当前 scene 的 `layout_prompt / panels / beat_sequence`
4. 再做视觉与对象层面的细化

## 先判断当前 scene 属于哪一类

在开始写 `steps` 之前，先判断当前幕更接近哪一种 scene 类型：

### 1. `whole_problem_scene`

特征：

- `question_scope = global`
- 主要服务整题，而不是某一问
- 常见于 `problem_intake` / `preview`

默认开场：

- 先让观众知道“这是整道题”
- 优先给出完整题目、题图、问法总览

### 2. `question_entry_scene`

特征：

- 当前 scene 开始进入某一问
- 或虽然 `workflow_step` 不是 `goal_lock`，但这是该问第一次成为主角

默认开场：

- 先让观众知道“现在在解哪一问”
- 优先给出当前问题目、相关条件、目标量

### 3. `question_continuation_scene`

特征：

- 仍在同一问内部推进
- 上一幕已经清楚呈现过该问目标

默认开场：

- 不必重新完整显示该问题目
- 但应有简洁的当前问提示或目标提示，避免观众丢失语境

### 4. `result_scene`

特征：

- 以结果回收、检查、总结、迁移为主
- 常见于 `check` / `recap` / `transfer`

默认开场：

- 先回到“这一幕要确认或回收的结论”

## 所有 scene 默认采用四段式局部结构

无论 scene 多短，优先沿着下面四段思考：

### `opening`

回答：

- 观众进入这一幕时，第一眼先看到什么
- 本幕的身份是什么：整题开场、当前问开场、当前问续推、结果回收

### `focus`

回答：

- 这一幕真正要锁定什么任务
- 哪些信息必须稳定上屏，而不能只靠字幕带过

### `development`

回答：

- 本幕主体内容如何推进
- `beat_sequence` 如何翻译成 `steps`

### `handoff`

回答：

- 本幕结束时，观众应该明确知道什么
- 下一幕将从哪里继续

## 三种推荐开场模板

这些是推荐模板，不是独立字段。你需要把它们翻译进 `on_screen_text`、`object_registry`、`steps` 与 `layout_contract`。

### A. `global_opening`

适用：

- `problem_intake`
- 某些全题 `preview`

推荐内容顺序：

1. 完整题目或完整题意版面
2. 题图 / 已知条件 / 问法总览
3. 有几问、每问求什么

推荐输出倾向：

- `on_screen_text` 以题干和问法为主
- `problem_panel` 应占据最稳定、最可读的位置
- 不要让复杂运动或大量公式抢走“先看清题”的角色

### B. `question_opening`

适用：

- `goal_lock`
- 某一问第一次出现时的 `model / method_choice / derive`

推荐内容顺序：

1. 当前是第几问
2. 当前问题目原文或完整改写
3. 与当前问直接相关的条件
4. 当前问要求的目标量

推荐输出倾向：

- 当前问题优先进入 `on_screen_text`
- `steps[0]` 优先做“当前问建立”，不要直接进入大图演示或公式推导

### C. `continuation_opening`

适用：

- 同一问的后续 scene

推荐内容顺序：

1. 当前仍在解哪一问
2. 前一幕已经得到的关键前提
3. 本幕要继续完成什么

推荐输出倾向：

- 可以只用简卡、标题条、目标条提示
- 不必重复整段问题原文

## workflow_step 的单幕细化模板

### `problem_intake`

推荐结构：

1. `opening`：完整题目呈现
2. `focus`：题图、条件、任务边界净化
3. `development`：整题问法总览
4. `handoff`：说明接下来如何进入正式求解

重点：

- 优先做“看清题”
- `on_screen_text` 优先承载题干和问法，而不是只放字幕

### `preview`

推荐结构：

1. `opening`：提醒这是整题预演
2. `focus`：先看发生了什么
3. `development`：轨迹、过程、关键事件快速回放
4. `handoff`：冻结到第一问入口

重点：

- 允许运动增强
- 但仍应保留整题身份提示，不要让观众忘记在看哪道题

### `goal_lock`

推荐结构：

1. `opening`：当前问题目展示
2. `focus`：筛出当前问相关条件
3. `development`：锁定本问目标量或中间目标
4. `handoff`：进入建模或选法

重点：

- 本幕更像“问题卡 + 条件卡 + 目标卡”
- 不要把完整推导链塞进这一幕

### `model`

推荐结构：

1. `opening`：当前问题简卡
2. `focus`：建立主图、坐标系、约束
3. `development`：补变量、方向、参考量
4. `handoff`：为后续推导提供稳定主图

重点：

- 如果这是该问第一次进入建模，优先采用 `question_opening`

### `method_choice`

推荐结构：

1. `opening`：当前问题简卡
2. `focus`：明确解法路线
3. `development`：解释为何采用该路线
4. `handoff`：转入 derive

### `derive`

推荐结构：

1. `opening`：当前问题简卡或本幕目标条
2. `focus`：锁定这一幕要推出的量
3. `development`：分步推导
4. `handoff`：产出中间量或最终量

重点：

- 如果这是该问第一次进入正式求解，优先先把当前问亮出来，再进入推导
- 不要让观众在未看见当前问目标时直接面对公式链

### `check`

推荐结构：

1. `opening`：回到当前问结果
2. `focus`：说明要检查什么
3. `development`：量纲/方向/极限/物理意义检查
4. `handoff`：准备总结或转下一问

### `recap`

推荐结构：

1. `opening`：当前问标题或本问结果板
2. `focus`：回顾关键结论
3. `development`：若有多问，说明与下一问的关系
4. `handoff`：自然转到下一问或结束

### `transfer`

推荐结构：

1. `opening`：方法标签或本题技巧名
2. `focus`：提炼可复用套路
3. `development`：提醒易错点或变式
4. `handoff`：结束视频

## JSON 字段映射指南

### `narration`

用途：

- 口播与字幕推进
- 负责陪伴式讲解

不要让它承担：

- 完整题目长期展示
- 当前问题目的稳定呈现
- 关键结论板的常驻显示

### `on_screen_text`

用途：

- 观众必须稳定看到的文字信息

优先放入这里的内容：

- 完整题目
- 当前问题目
- 当前问目标量
- 本幕关键结论

### `object_registry`

优先显式定义这些对象：

- 题目面板
- 当前问题卡
- 条件摘录板
- 主图骨架
- 推导公式组
- 结果总结板

### `steps`

写法原则：

- 优先把 `beat_sequence` 翻译成 step
- `step_01` 通常承担 `opening`
- 不要一上来就跳到最复杂的推导或运动

### `layout_contract`

写法原则：

- 题目、当前问题、结果板要有稳定区域
- 字幕区只给 narration 使用
- 不要让题目文本挤进 subtitle zone

### `motion_contract`

写法原则：

- `preview` 可以更强
- `problem_intake / goal_lock` 通常应弱于文字信息
- 当教学重点是“看清题”时，运动应服务阅读，而不是压过阅读
- `steps` 决定“什么时候动”，`motion_contract` 决定“这一步怎么动”
- 如果某一步没有运动，就不要为它硬塞 motion 段
- 如果某一步有运动，优先把运动明确挂到该 `step_id`，而不是再创造独立于 step 的全局时间轴

## 教学视频优先级提醒

如果你只能优先保证一件事，优先保证观众知道当前在看什么题、当前在解哪一问。

因此：

- 整题开场优先完整题目可读
- 每一问第一次进入时优先当前问题目可读
- 推导与动画都应建立在“观众知道当前任务是什么”的前提上
