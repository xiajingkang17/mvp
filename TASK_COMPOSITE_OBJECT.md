# CompositeObject 动态组图任务文档

## 1. 目标与共识

- 题意图在外层只算 **1 个 object**，占 **1 个 slot**。
- 每个 scene 先在**独立内部坐标系**绘制（固定度量），再整体等比缩放放入 slot。
- LLM 可以输出坐标；非质点运动使用锚点/接触点约束反算中心点，避免穿轨道。
- 不按题改源码；一次性建设通用机制，后续题目由 LLM 现场生成图形 IR。

## 2. 非目标

- 本阶段不做完整物理仿真引擎。
- 本阶段不覆盖全部题型，只先打通通用机制 + 典型题。

## 3. 总体方案

- 新增通用对象类型：`CompositeObject`。
- `CompositeObject.params.graph` 由 LLM 现场生成，包含：
  - `space`（内部坐标系）
  - `parts`（基础组件实例）
  - `tracks`（轨道几何）
  - `constraints`（关系约束）
  - `motions`（关键帧或参数运动）
- 渲染流程：
  1. 构建 parts
  2. 约束求解得到内部位姿
  3. 聚合为单个 `VGroup`
  4. 外层按 slot 等比缩放并摆放

## 4. 分阶段任务清单

### P0. 规范冻结（文档确认）

- [x] 冻结 IR 字段命名、单位、坐标轴方向、角度单位（度/弧度）
- [x] 冻结“外层只认一个 object”的 pipeline 约束

产出：

- `COMPOSITE_IR_SPEC.md`（P0 冻结规范，作为后续 P1-P8 的唯一协议来源）

验收标准：

- 评审通过 `COMPOSITE_IR_SPEC.md` 后进入 P1

---

### P1. Schema 与枚举

- [ ] `configs/enums.yaml` 增加 `CompositeObject`
- [ ] 新增 `schema/composite_graph_models.py`（Pydantic）
- [ ] `validate_plan` 增加 `CompositeObject.params.graph` 校验

建议文件：

- `configs/enums.yaml`
- `schema/composite_graph_models.py`
- `pipeline/validate_plan.py`
- `tests/test_composite_schema.py`

验收标准：

- `CompositeObject` 可通过 schema 校验
- 非法 graph（缺字段/错类型）能清晰报错

---

### P2. LLM 输出约束（先静态图）

- [ ] 更新 LLM2 prompt：物理图优先输出 1 个 `CompositeObject`
- [ ] graph 先启用 `parts + constraints`（暂不强制 motion）
- [ ] 更新 LLM3 prompt：只对整图 object 做 slot 布局

建议文件：

- `prompts/llm2_scene_draft.md`
- `prompts/llm3_scene_layout.md`
- `pipeline/run_llm2.py`

验收标准：

- demo case 中 scene_draft 的题意图只出现 1 个 `CompositeObject`

---

### P3. CompositeObject 构建器

- [ ] 新增 `components/composite/object_component.py`
- [ ] 支持 graph 读取、子组件构建、聚合为 `VGroup`
- [ ] 第一版禁止递归嵌套 `CompositeObject`

建议文件：

- `components/composite/object_component.py`
- `render/registry.py`
- `tests/test_composite_registry.py`

验收标准：

- 最小 graph 可渲染为单个 `VGroup`

---

### P4. 静态约束求解（核心）

- [ ] 实现基础约束：`attach` `on_segment` `midpoint` `align_axis` `distance`
- [ ] 支持 `seed_pose + 约束修正`
- [ ] 输出 `resolved_pose`（用于调试）

建议文件：

- `render/composite/solver.py`
- `render/composite/types.py`
- `tests/test_composite_solver_static.py`

验收标准：

- 斜面-BC-弹簧-P/Q-A/B/C 静态关系正确
- 约束残差在阈值内

---

### P5. 非质点轨道运动（锚点驱动）

- [ ] 每个可运动 part 支持锚点（如 `bottom_center`）
- [ ] 新增 `on_track(part, anchor, track, s)` 运动约束
- [ ] 用接触点反算中心点与姿态，避免“中心点穿轨道”

建议文件：

- `render/composite/anchors.py`
- `render/composite/tracks.py`
- `render/composite/motion.py`
- `tests/test_composite_motion_on_track.py`

验收标准：

- 滑块沿斜面/水平轨道运动时不穿透轨道

---

### P6. 外层 slot 变换

- [ ] 统一流程：内部绘制 -> 测 bbox -> 等比缩放 -> 放入 slot
- [ ] 字体、线宽先跟随整体缩放（暂不设下限）

建议文件：

- `render/plan_scene.py`
- `tests/test_composite_slot_fit.py`

验收标准：

- 同一 CompositeObject 在不同 layout 下内部关系不变

---

### P7. 容错与可观测性

- [ ] 求解失败降级到 seed_pose（不中断渲染）
- [ ] 输出调试文件：`resolved_pose.json`、`constraint_residuals.json`
- [ ] 错误信息定位到 `part_id/constraint_id`

建议文件：

- `render/composite/debug.py`
- `pipeline/validate_plan.py`

验收标准：

- 异常 case 不崩溃，且能给出明确诊断

---

### P8. Demo 验证（当前题）

- [ ] `cases/demo_001` 迁移为 1 个 `CompositeObject` 表达题意图
- [ ] scene 仅放这个 object 到 1 个 slot
- [ ] 渲染验证关系正确（斜面接水平面、Q 在 BC 中点、C 处弹簧）

验收标准：

- `python -m pipeline.validate_plan cases/demo_001/scene_plan.json` 通过
- demo 渲染可用且题意关系正确

## 5. 执行规则

- 每次只做一个阶段（或一个子项），避免大爆改。
- 每完成一项必须包含：
  1. 代码变更
  2. 对应测试
  3. 命令验证
  4. 结果汇报（改了哪些文件 + 是否通过）

## 6. 建议推进顺序

- 第一轮：`P1 -> P3 -> P4 -> P8`（先打通静态单对象链路）
- 第二轮：`P5 -> P6 -> P7`（补运动、适配、容错）
