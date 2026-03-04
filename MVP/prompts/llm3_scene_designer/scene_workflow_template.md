# 单幕内容细化模板（LLM3）

本文件只回答一件事：

给定 llm2 的一个 scene，大纲已经定了，这一幕内部该怎么展开成内容设计稿。

它不负责布局，不负责 zone，不负责坐标。

## 基本定位

- llm2 决定 scene 的职责
- llm3 决定这一幕先讲什么、后讲什么、对象怎么随 step 推进

## 单幕默认四段式

每个 scene 默认按这四段思考：

1. `opening`
2. `focus`
3. `development`
4. `handoff`

## 三种开场

### 1. `global_opening`

适用于：

- `problem_intake`
- 某些整题 `preview`

优先让观众知道：

- 这是整道题
- 题目是什么
- 一共几问

### 2. `question_opening`

适用于：

- `goal_lock`
- 某一问第一次进入的 `model / method_choice / derive`

优先让观众知道：

- 现在在解哪一问
- 当前问题目是什么
- 目标量是什么

### 3. `continuation_opening`

适用于：

- 同一问的后续 scene

优先让观众知道：

- 还在解哪一问
- 上一幕已经得到什么
- 这幕接着做什么

## 各类 workflow_step 的内容结构

### `problem_intake`

- opening：完整题目
- focus：题图与条件
- development：分问总览
- handoff：转入第一问

### `preview`

- opening：整题预演
- focus：关键过程
- development：关键节点
- handoff：转入正式求解

### `goal_lock`

- opening：当前问题目
- focus：当前问相关条件
- development：目标量锁定
- handoff：进入建模或推导

### `model`

- opening：当前问简卡
- focus：建立主图
- development：补变量和约束
- handoff：为推导准备

### `method_choice`

- opening：当前问简卡
- focus：说明采用哪条解法
- development：解释为什么
- handoff：转入推导

### `derive`

- opening：当前问简卡或当前目标
- focus：本幕要推出哪个量
- development：分步推导
- handoff：得到中间量或结论

### `check`

- opening：回到当前结果
- focus：说明检查对象
- development：验证
- handoff：准备总结

### `recap`

- opening：本问标题或结果条
- focus：本问结论
- development：必要时连接下一问
- handoff：转场

### `transfer`

- opening：方法标签
- focus：提炼套路
- development：易错点或变式
- handoff：结束

## 输出落点

你需要把上面的结构翻译到：

- `narration`
- `on_screen_text`
- `object_registry`
- `steps`
- `motion_contract`

不要输出任何布局字段。
