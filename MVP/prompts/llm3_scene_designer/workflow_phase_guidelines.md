# workflow_step 内容约束（LLM3）

输入中的当前 scene 来自 llm2 scene planner，其中最重要的字段是：

- `workflow_step`
- `scene_goal`
- `entry_requirement`
- `key_points`
- `scene_outputs`
- `handoff_to_next`
- `panels`
- `beat_sequence`

其中 `workflow_step` 不是参考信息，而是当前 scene 的教学角色。

## 总原则

1. 先服从 `workflow_step`，再细化 step。
2. 不要把不属于当前 step 的职责混进来。
3. `scene_goal` 决定本幕要完成什么，`key_points` 决定本幕必须讲清哪些核心点。
4. `entry_requirement` 决定这幕开场的认知前提，`scene_outputs / handoff_to_next` 决定这幕结束时要交出去什么。
5. `panels` 与 `beat_sequence` 是本幕的内容组织提示，你应尊重它们，但不要把它们翻译成布局坐标。
6. scene 仍然对象独立：`entry_state` 与 `exit_state` 都为空。

## 各 workflow_step 的内容职责

### `problem_intake`

- 完整呈现题目、问法、题图、已知未知
- 不要展开正式推导

### `preview`

- 先让观众看懂整体过程
- 不要塞大量公式链

### `goal_lock`

- 锁定当前问
- 筛出相关条件
- 明确目标量

### `model`

- 把语言条件变成主图、变量、约束
- 不要提前完成整套推导

### `method_choice`

- 明确解法路线
- 说明为什么这样解

### `derive`

- 完成核心推导
- 分步推进
- 如果有两行及以上推导链，steps 应体现逐行推进，而不是一句“展示推导”

### `check`

- 验证结果
- 解释结果意义

### `recap`

- 回收本问结论
- 为下一问或结尾做承接

### `transfer`

- 提炼方法
- 提醒易错点

## 对 steps 的要求

1. `steps` 是本幕内容推进的主时间轴。
2. `beat_sequence` 如果已经给出先后顺序，你应尽量沿这个顺序展开。
3. `derive` 类 scene 中，公式链应按“写式子 / 代入 / 化简 / 得结论”的顺序拆进 steps。
4. `problem_intake` 与 `goal_lock` 中，题目与当前问应优先进入 `on_screen_text`。

## 与 motion 的关系

1. `steps` 决定什么时候动。
2. `motion_contract` 决定这一步怎么动。
3. 如果某一步没有运动，就不要硬塞 motion。
