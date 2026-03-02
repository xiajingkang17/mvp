# 布局契约执行规范（LLM4）

输入中的 `scene_design.layout_contract` 是生成期硬约束。你必须在生成阶段消化它，而不是把整份 schema 字典留到最终代码里。

## 必须执行

1. 解析 `layout_contract.zones`，每个 zone 必须有 `role`。
2. 解析 `layout_contract.objects`，按 `zone` 放置对象。
3. 解析 `layout_contract.step_visibility`，它只表示“参与布局计算的对象”，不表示创建或销毁。
4. 标题、公式、总结、字幕的位置必须从 zone 推导；最终代码里应保留 primitive zone rect，而不是 `layout_contract = {...}`。
5. 如果 scene 提供了 `subtitle` zone，`steps[*].narration` 必须实际渲染为 subtitle 对象并放入该区域；如果 scene 没有 `subtitle` zone，就不要额外发明第二个字幕区。
6. 优先复用 `fit_in_zone / place_in_zone / layout_formula_group / show_subtitle`。

## role 语义

- `main`: 主图、轨迹、示意图
- `formula`: 公式、推导、结论式
- `title`: 标题、章节提示
- `summary`: 总结、结论
- `subtitle`: 字幕、讲解文本
- `aux`: 辅助说明、标签
- `animation_only`: 只适合纯过程展示型 scene

## 与显隐逻辑的边界

- `steps[*].object_ops` 是 step 级唯一显隐真源。
- `exit_state.objects_on_screen` 是 scene 级唯一收场真源。
- `layout_contract` 只管放置与布局参与对象，不负责生命周期。

## 字幕执行硬规则

1. `subtitle` zone 不是必填；有些 scene 可以完全没有字幕区。
2. 如果 scene 提供了字幕区，它是固定保留区。编译时必须严格按设计执行，不允许缩小，也不允许其他 zone 与之重叠。
3. 字幕只能通过 `show_subtitle(...)` 渲染，不要手写带自定义偏移的字幕布局；额外文字说明应放在 `title`、`summary`、`aux` 等其他 role 对应区域。
4. 如果 scene 使用的是来自 `layout_contract` 的归一化 zone rect，就要么全程保持这套坐标契约，要么正确换算成 Manim 世界坐标；不要随意混用两套坐标。
5. 如果字幕文字只有靠大幅缩小字号才能塞进字幕区，不要压缩字幕区；应把原始 narration 交给运行时 helper 自动拆分成多段顺序显示。
6. `steps[*].narration` 在主链路中应视为单个字符串，不要在 codegen 阶段自行发明第二套字幕分段协议。
