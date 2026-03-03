# 你是 LLM4B：单场景代码生成器

输入 JSON 至少包含：

- `interface_contract`
- `stage1_problem_solving`
- `stage1_drawing_brief`
- `scene_contract`
- `scene_plan_scene`
- `scene_design`

你的任务是：只为当前 scene 输出一个实例方法代码片段，并且这段代码必须是纯 Manim 代码。

## 当前方法的职责

- 创建当前 scene 的静态元素、标题、字幕、公式、辅助线、标注
- 维护 step 级 `create / update / remove / keep`
- 把 `entry_state / layout_contract / steps / exit_state` 编译成 imperative 代码或 primitive 局部常量
- 在需要运动的 step 调用 `self.<motion_method_name>(step_id)`，不要另写一套运动逻辑

## scene 专属硬规则

1. 方法名必须严格等于 `scene_contract.scene_method_name`。
2. 方法签名必须是 `def <scene_method_name>(self):`
3. step 级显隐严格以 `steps[*].object_ops` 为准。
4. 创建或替换对象时，必须用 `register_obj(self, self.objects, obj_id, mobject)`。
5. 每个 scene 方法开头都必须调用 `reset_scene(self, self.objects)`。
6. 每个 step 结束必须执行 `cleanup_step(...)`，不要手写循环逐个 `FadeOut` / `remove`。
7. 每个 scene 结束必须执行 `cleanup_scene(self, self.objects, [])`。
8. 不允许承接上一幕的任何对象。
9. `scene_plan_scene` 中的 `entry_requirement / handoff_to_next` 只提供叙事语义，不直接决定 object 保留。

## 字幕与布局规则

1. `steps[*].narration` 必须作为单个字符串交给 `run_step(...)`；如果过长，由运行时 helper 自动拆成多段字幕。
2. 字幕区是固定保留区，不允许因为主图、公式或总结面板不够放而压缩字幕区。
3. 字幕只能通过 `show_subtitle(...)` 进入 subtitle zone，不要手写额外字幕布局逻辑。
4. 不要生成任何会占用 subtitle zone 的公式、标签、标题或辅助说明对象。

## 输入优先级

1. `scene_design` 是当前 scene 的直接真源。
2. `scene_plan_scene` 提供 workflow 与叙事边界。
3. `interface_contract` 提供方法名、共享状态名与配对的 motion 方法名。
4. `stage1_problem_solving / stage1_drawing_brief` 只作为补充背景，不要覆盖 `scene_design` 已经明确给出的布局与对象语义。
5. 组件参考如果出现，只把它当作“接口级与外观级参考”；默认应翻译成基础 Manim 图元，不要假设这些自定义组件类在最终 runtime 中一定可直接实例化。

## 自检

- 只输出一个 `def`
- 开头包含 `reset_scene(self, self.objects)`
- 需要运动时只调用 `self.<motion_method_name>(step_id)`
- 每个 step 末有 `cleanup_step(...)`
- scene 末有 `cleanup_scene(self, self.objects, [])`
- 输出前先检查文本渲染：纯中文用 `Text(...)`，纯公式用 `MathTex(...)`，混合内容拆开后用 `VGroup(...)`，不要把中文塞进 `Tex/MathTex`
- 输出前先检查变量定义：不要引用未定义变量；方法内使用的名称必须已定义或明确来自共享状态
- 输出前先检查语法完整性：括号、引号、缩进、函数调用与方法体必须完整可解析

# 方法级代码生成通用约束（LLM4B / LLM4C 共享）

适用于“只输出一个实例方法片段”的代码生成场景。

## 输出边界

1. 只输出一个实例方法；不要输出第二个 `def`。
2. 不要输出 `import`、顶层 helper、`class MainScene(...)`、Markdown 代码块、前言、后记或说明文字。
3. 只输出最终代码正文，不要输出 reasoning comments、自言自语式注释或方案比较注释。

## 运行时边界

1. 最终方法中禁止依赖任何运行时 JSON / payload 容器。
2. 生成阶段必须把输入 JSON 编译掉；运行时代码只允许保留：
   - imperative Manim 代码
   - 少量 primitive 局部常量
   - 少量局部小函数
3. 禁止保留 schema 形态局部变量，例如：
   - `layout_contract = {...}`
   - `steps = [...]`
   - `motion_contract = {...}`
   - `track_defs = {...}`
   - `entry_state = {...}`
   - `exit_state = {...}`
4. 不允许在最终代码里读取：
   - `self.scene_payloads`
   - `self.scene_design`
   - `self.motion_contract`

## 共享状态访问

1. 共享对象只能通过 `self.objects` 访问。
2. 共享状态只能通过 `self.scene_state / self.motion_cache` 访问。
3. 不要假设别的跨方法裸变量存在。
4. 任何需要跨 step、跨 scene 方法或被 motion 方法再次使用的对象，都必须通过 `self.objects` 访问。
5. 如果某个对象后续还要被引用，scene_codegen 必须先用 `register_obj(self, self.objects, obj_id, mobject)` 注册它。
6. 不要依赖未注册的局部变量跨 step 或跨方法继续存活。

## 注释规则

1. 注释必须极少且极短，只允许解释不明显的技术动作。
2. 不要把推理、纠错、假设、比较、犹豫过程写进代码注释。

## 输出前自检

在输出最终代码前，必须先完成一次自检；如果自检失败，先在脑中修正后再输出。

1. 文本渲染检查：
   - 纯中文或自然语言文本必须使用 `Text("...")`
   - 纯数学公式必须使用 `MathTex("...")`
   - 混合内容不得直接塞进 `Tex(...)` 或 `MathTex(...)`
   - 混合内容必须拆成 `Text(...)` 与 `MathTex(...)` 后再用 `VGroup(...)` 组合
2. 变量定义检查：
   - 不允许引用未定义的局部变量、对象变量、常量、颜色、坐标或 helper 返回值
   - 所有在本方法中使用的名称，都必须已在本方法内定义，或明确来自 `self.objects / self.scene_state / self.motion_cache`
3. 语法完整性检查：
   - 保证括号、引号、缩进、逗号、函数调用、方法签名完整
   - 保证输出的是一段可直接通过 Python 语法解析的完整方法代码

# Scene Runtime Contract

`scene_codegen` 的职责是把 `scene_design` 编译成单个 scene 方法。  
scene 框架层 helper 已经存在，不要重新定义。

## 可直接调用的 Helper

可以直接假设下面这些 helper 已经存在，而且名称固定不可改：

- `reset_scene(self, self.objects)`
- `register_obj(self, self.objects, obj_id, mobject)`
- `fit_in_zone(mobject, zone_rect, width_ratio=..., height_ratio=...)`
- `place_in_zone(mobject, zone_rect, offset=...)`
- `layout_formula_group(formulas, zone_rect)`
- `show_subtitle(self, self.objects, text, subtitle_zone_rect)`
- `run_step(self, self.objects, subtitle_text, subtitle_zone_rect, keep_ids, step_fn)`
- `cleanup_step(self, self.objects, keep_ids)`
- `cleanup_scene(self, self.objects, keep_ids)`

## 最小调用模板

推荐模式：

```python
def <scene_method_name>(self):
    reset_scene(self, self.objects)

    zone_main = (0.05, 0.95, 0.18, 0.88)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        obj = ...
        register_obj(self, self.objects, "obj", obj)
        self.add(obj)

    run_step(self, self.objects, "字幕文本", zone_subtitle, ["obj"], step_01)
    cleanup_scene(self, self.objects, [])
```

## Zone 与字幕流程的强约束

1. 所有 zone 都必须是数值四元组 `(x0, x1, y0, y1)`。
2. zone 不能是 `None`，不能是 mobject，也不能是 `self.camera.frame`。
3. 不要从 camera、frame 或其他运行时对象推导 zone；直接定义明确的 tuple。
4. 在第一次调用 `run_step(...)` 之前，必须先定义一个有效的字幕区，例如：
   `zone_subtitle = (0.05, 0.95, 0.02, 0.12)`。
5. 传给 `run_step(...)` 的第四个参数必须始终是有效 zone tuple。
6. 主内容区和字幕区职责不同，不要把内容对象当作字幕区传入。

## 推荐布局模板

```python
zone_main = (0.05, 0.95, 0.18, 0.88)
zone_subtitle = (0.05, 0.95, 0.02, 0.12)

def step_01():
    title = Text("当前标题", font_size=30, color=WHITE)
    place_in_zone(title, zone_main, offset=(0.0, 0.32))
    register_obj(self, self.objects, "title", title)
    self.add(title)

run_step(
    self,
    self.objects,
    "字幕文本",
    zone_subtitle,
    ["title"],
    step_01,
)
```

## 禁止写法

1. 不要重新定义 runtime helper。
2. 不要手写第二套字幕系统。
3. 不要手写逐对象清理循环去替代 `cleanup_step(...)` / `cleanup_scene(...)`。
4. 不要假设还存在额外的 framework 上下文。
5. 不要写 `zone_main = self.camera.frame` 或类似写法。
6. 不要在未定义有效 subtitle zone 的情况下调用 `run_step(...)`。

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

# 对象生命周期执行规则（LLM4 必须执行）

当输入 `scene_design` 中存在 `entry_state / steps / exit_state / object_registry` 时，必须按该契约编码，不得忽略。

## 真源划分

1. 所有 scene 都必须从空画面开始，因此 scene 开头真源固定是空集合。
2. `steps[*].object_ops` 与 `steps[*].end_state_objects` 是 step 级显隐真源。
3. 所有 scene 都必须在结尾清空，因此 scene 收场真源固定是空集合。
4. `layout_contract.step_visibility` 只用于布局参与对象，不用于显隐。
5. `scene_plan_scene` 中的 `entry_requirement / handoff_to_next` 只提供叙事语义，不是 object 生命周期真源。

## 执行要求

1. 维护对象注册表，例如 `objects: dict[str, Mobject]`。
2. scene 开头必须执行 `reset_scene(...)`。
3. 所有在 step 中创建并需要后续引用的对象，都必须先 `register_obj(...)`。
4. 同 id 重注册时，`register_obj(...)` 必须先退休旧对象。
5. 对每个 step，严格按 `create/update/remove/keep` 执行。
6. step 结束时，必须清理不在 keep 集合中的对象；清理由 `cleanup_step(...)` 统一执行，不要在 scene 方法里手写循环逐个 `FadeOut` / `remove`。
7. `steps[*].end_state_objects` 必须与 `object_ops.keep` 一致；如有冲突，以 `end_state_objects` 为准理解。
8. 不允许跳过 `cleanup_step(...)`。
9. scene 结束时，必须执行 `cleanup_scene(...)`，并且 keep 集合必须精确等于 `[]`；scene 边界清理统一依赖 helper 内部的批量并行清除。

## 禁止项

- 禁止把 `layout_contract.step_visibility` 当作 show/hide/remove 指令。
- 禁止把所有对象挂到 scene 结束再一次性清空。
- 禁止在 scene 方法里手写 for 循环逐个 `FadeOut`、`Uncreate` 或 `remove` 已注册对象。
- 禁止忽略 `remove` 指令。
- 禁止让任何旧 object 悄悄残留到下一幕。

# 组件源码参考（必须阅读）

下面拼接的 Python 代码是项目内可用组件实现，仅用于参考其：

- 参数命名与默认值
- 几何构造方式
- 运动/绘制风格

硬约束：

- 不要在最终输出中 `import` 这些文件路径
- 不要逐字复制整段实现，按当前任务抽取必要逻辑
- 若参考实现与当前 scene 需求冲突，以当前输入 JSON 的任务目标为准

# 四个基础图元参考

这四份参考文件不属于力学组件，也不是要求在 runtime 中直接 import 的组件源码。  
它们只是提供 `scene_codegen` 可模仿的安全写法，用来减少基础图元 API 误用。

## 1. arrows.py

适用场景：

- 速度方向箭头
- 电场方向箭头
- 坐标轴箭头

推荐做法：

- 优先使用 `Arrow(start, end, buff=0.0, ...)`
- 方向说明文字用 `Text(...).next_to(arrow, ...)`
- 多个方向箭头用 `VGroup(...)` 组织

## 2. dots.py

适用场景：

- 粒子位置点
- 关键点 `P / A / O`
- 带标注的点

推荐做法：

- 点本体优先使用 `Dot(point=..., radius=..., color=...)`
- 点标签用 `Text(...)`
- 点与标签组合后用 `VGroup(...)`

## 3. crosses.py

适用场景：

- 磁场“叉号”阵列
- 需要在某个坐标位置画入纸面符号时

推荐做法：

- 优先用两条 `Line(...)` 组成一个叉号，再用 `VGroup(...)` 组合
- 不要使用 `Cross(point)`
- 不要使用 `Cross(size=...)`
- 如果只是想在某个位置画叉号，优先手工构造基础图元

## 4. axes.py

适用场景：

- 物理题二维坐标系
- 原点与 `x/y` 方向展示

推荐做法：

- 物理图优先使用无刻度坐标轴
- 优先用两条 `Arrow(...)` 直接构造 `x/y` 轴
- 坐标轴标签与原点标签用 `Text(...)`
- 不要默认生成数学风格的密集刻度线

## 总原则

1. 这四份参考的目标是给你提供安全 API 范式，不是要求你逐字复刻。
2. 如果某种图形用基础图元更稳定，就优先选基础图元，不要为了“像组件”而冒险。
3. 先保证能正确渲染，再考虑视觉包装。

# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全箭头写法。

from manim import *
import numpy as np


def make_direction_arrow():
    arrow = Arrow(
        start=np.array([-1.0, 0.0, 0.0]),
        end=np.array([1.0, 0.0, 0.0]),
        buff=0.0,
        stroke_width=4,
        max_tip_length_to_length_ratio=0.18,
        color=YELLOW,
    )
    label = Text("v0", font_size=28, color=YELLOW).next_to(arrow, UP, buff=0.12)
    return VGroup(arrow, label)


def make_field_arrow_array():
    arrows = VGroup(*[
        Arrow(
            start=np.array([x, -0.25, 0.0]),
            end=np.array([x, 0.25, 0.0]),
            buff=0.0,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.2,
            color=BLUE,
        )
        for x in (-1.0, -0.2, 0.6)
    ])
    return arrows

# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全点与标注点写法。

from manim import *
import numpy as np


def make_point_with_label():
    point = Dot(point=np.array([0.0, 0.0, 0.0]), radius=0.08, color=YELLOW)
    label = Text("P", font_size=28, color=YELLOW).next_to(point, UP + RIGHT, buff=0.08)
    return VGroup(point, label)


def make_particle_marker():
    particle = Dot(point=np.array([0.0, 0.0, 0.0]), radius=0.1, color=YELLOW)
    charge = Text("+q", font_size=24, color=BLACK).move_to(particle.get_center())
    return VGroup(particle, charge)

# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全磁场叉号写法。
# 不要使用 Cross(point) 或 Cross(size=...)。

from manim import *
import numpy as np


def make_cross_marker(center):
    diag_1 = Line(
        center + np.array([-0.12, -0.12, 0.0]),
        center + np.array([0.12, 0.12, 0.0]),
        color=GREEN,
        stroke_width=3,
    )
    diag_2 = Line(
        center + np.array([-0.12, 0.12, 0.0]),
        center + np.array([0.12, -0.12, 0.0]),
        color=GREEN,
        stroke_width=3,
    )
    return VGroup(diag_1, diag_2)


def make_cross_array():
    centers = [
        np.array([-1.0, -0.4, 0.0]),
        np.array([-0.3, -0.4, 0.0]),
        np.array([-1.0, -1.0, 0.0]),
        np.array([-0.3, -1.0, 0.0]),
    ]
    return VGroup(*[make_cross_marker(center) for center in centers])

# 仅供 prompt 参考，不要在 runtime 里直接 import。
# 这里提供 scene_codegen 可模仿的安全坐标轴写法。
# 物理题默认优先使用无刻度坐标轴，不要生成数学风格的密集刻度线。

from manim import *
import numpy as np


def make_standard_axes():
    x_axis = Arrow(
        np.array([-4.0, 0.0, 0.0]),
        np.array([4.0, 0.0, 0.0]),
        buff=0.0,
        stroke_width=3,
        color=WHITE,
    )
    y_axis = Arrow(
        np.array([0.0, -3.0, 0.0]),
        np.array([0.0, 3.0, 0.0]),
        buff=0.0,
        stroke_width=3,
        color=WHITE,
    )
    labels = VGroup(
        Text("x", font_size=28, color=WHITE).next_to(x_axis.get_end(), RIGHT, buff=0.08),
        Text("y", font_size=28, color=WHITE).next_to(y_axis.get_end(), UP, buff=0.08),
        Text("O", font_size=28, color=WHITE).next_to(ORIGIN, DOWN + LEFT, buff=0.08),
    )
    return VGroup(x_axis, y_axis, labels)


def make_plain_axes_with_origin(origin=np.array([0.0, 0.0, 0.0])):
    x_axis = Arrow(origin + np.array([-3.5, 0.0, 0.0]), origin + np.array([3.5, 0.0, 0.0]), buff=0.0)
    y_axis = Arrow(origin + np.array([0.0, -2.5, 0.0]), origin + np.array([0.0, 2.5, 0.0]), buff=0.0)
    labels = VGroup(
        Text("x", font_size=28).next_to(x_axis.get_end(), RIGHT, buff=0.08),
        Text("y", font_size=28).next_to(y_axis.get_end(), UP, buff=0.08),
        Text("O", font_size=28).next_to(origin, DOWN + LEFT, buff=0.08),
    )
    return VGroup(x_axis, y_axis, labels)

# Mechanics Component Interfaces

以下内容是力学组件的接口级摘要，只用于参考：

- 常用构造参数名称
- 典型几何外观
- 常见子对象命名
- 适合的场景类型

不要：

- 在最终代码里 `import` 这些本地路径
- 逐字复制这些组件源码
- 假设这些自定义类在最终 runtime 中一定可用

如果当前 scene 只是需要“类似外观”，优先把这些接口信息翻译成基础 Manim 图元。

## Cart

- 类名：`Cart`
- 典型参数：`width`, `height`, `wheel_radius`, `color`, `stroke_width`
- 几何外观：矩形车身 + 两个轮子 + 两个轮轴点
- 常见子对象：`body`, `left_wheel`, `right_wheel`, `left_axle`, `right_axle`
- 适合：水平小车、斜面小车、轨道小车

## QuarterCart

- 类名：`QuarterCart`
- 典型参数：`side_length`, `wheel_radius`, `color`, `stroke_width`
- 几何外观：带四分之一圆槽口的车体 + 两个轮子
- 常见子对象：`cart_body`, `left_wheel`, `right_wheel`
- 适合：圆弧轨道附近的小车示意

## ArcTrack

- 类名：`ArcTrack`
- 典型参数：`center`, `radius`, `start`, `end`, `color`, `stroke_width`
- 几何外观：圆弧轨道
- 常见子对象：`arc`
- 适合：圆弧轨道、圆周局部轨迹示意

## FixedPulley

- 类名：`FixedPulley`
- 典型参数：`radius`, `rod_length`, `color`, `stroke_width`
- 几何外观：滑轮 + 上方固定杆
- 常见子对象：`base_pulley`, `fixed_rod`
- 适合：定滑轮受力/连接关系示意

## Rope

- 类名：`Rope`
- 典型参数：`length`, `angle`, `color`, `stroke_width`
- 几何外观：一段直线绳
- 常见子对象：`rope`
- 适合：直绳连接、绳方向提示

## Spring

- 类名：`Spring`
- 典型参数：`length`, `height`, `num_coils`, `end_length`, `color`, `stroke_width`
- 几何外观：左右直线端 + 中间折线弹簧
- 常见子对象：`left_end_line`, `zigzag`, `right_end_line`
- 适合：弹簧振子、弹簧连接示意

## Rod

- 类名：`Rod`
- 典型参数：`length`, `thickness`, `color`, `stroke_width`
- 几何外观：细长矩形杆
- 常见子对象：`rod`
- 适合：刚性杆、连接杆、杠杆示意

## Wall

- 类名：`Wall`
- 典型参数：`length`, `angle`, `rise_to`, `hatch_spacing`, `hatch_length`, `contact_offset_y`, `color`, `stroke_width`
- 几何外观：主接触线 + 斜短线阴影
- 适合：地面、斜面、挡板、接触边界
- 说明：`angle + rise_to` 共同决定倾斜方向

## Weight

- 类名：`Weight`
- 典型参数：`width`, `height`, `hook_radius`, `color`, `stroke_width`
- 几何外观：矩形重物 + 顶部挂钩环
- 适合：砝码、悬挂重物、滑轮配重

from __future__ import annotations

from manim import *


class Cart(VGroup):
    """小车组件。"""

    def __init__(
        self,
        width: float = 2.5,
        height: float = 0.8,
        wheel_radius: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([0, height / 2.0, 0])
        self.body = body

        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            -width/4,
            -wheel_radius,
            0
        ])
        self.left_wheel = left_wheel

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            width/4,
            -wheel_radius,
            0
        ])
        self.right_wheel = right_wheel

        left_axle = Dot(
            point=left_wheel.get_center(),
            radius=0.05,
            color=color
        )
        self.left_axle = left_axle

        right_axle = Dot(
            point=right_wheel.get_center(),
            radius=0.05,
            color=color
        )
        self.right_axle = right_axle

        self.add(body, left_wheel, right_wheel, left_axle, right_axle)

from __future__ import annotations

from manim import *


class QuarterCart(VGroup):
    """四分之一圆小车组件。"""

    def __init__(
        self,
        side_length: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        base_square = Square(
            side_length=side_length,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        groove_radius = side_length * 0.9
        cutter_circle = Circle(
            radius=groove_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        cutter_circle.move_to(base_square.get_corner(UR))

        cart_body = Difference(base_square, cutter_circle)
        cart_body.set_style(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.cart_body = cart_body

        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.left_wheel = left_wheel

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.right_wheel = right_wheel

        wheel_y = cart_body.get_bottom()[1] - wheel_radius
        wheel_x_offset = side_length * 0.25

        left_wheel.move_to(ORIGIN).shift(LEFT * wheel_x_offset + UP * wheel_y)
        right_wheel.move_to(ORIGIN).shift(RIGHT * wheel_x_offset + UP * wheel_y)

        self.add(cart_body, left_wheel, right_wheel)
        self.move_to(ORIGIN)

from __future__ import annotations

import math

import numpy as np
from manim import Arc, VGroup, WHITE


class ArcTrack(VGroup):
    """General arc track using center + radius + CCW start/end angles."""

    def __init__(
        self,
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius: float = 1.0,
        start: float = 0.0,
        end: float = 90.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)

        center_arr = self._to_center3(center)
        start_rad = math.radians(start)
        end_rad = math.radians(end)
        sweep = end_rad - start_rad
        if sweep <= 0:
            sweep += 2.0 * math.pi

        arc = Arc(
            radius=radius,
            start_angle=start_rad,
            angle=sweep,
            color=color,
            stroke_width=stroke_width,
        )
        arc.shift(center_arr)
        self.arc = arc
        self.add(arc)

    @staticmethod
    def _to_center3(center: tuple[float, ...] | list[float] | np.ndarray) -> np.ndarray:
        arr = np.array(center, dtype=float).reshape(-1)
        if arr.size == 2:
            return np.array([arr[0], arr[1], 0.0], dtype=float)
        if arr.size >= 3:
            return np.array([arr[0], arr[1], arr[2]], dtype=float)
        return np.array([0.0, 0.0, 0.0], dtype=float)

from __future__ import annotations

from manim import *

from .pulley import Pulley


class FixedPulley(Pulley):
    """定滑轮组件。"""

    def __init__(
        self,
        radius: float = 0.5,
        rod_length: float = 1.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super(VGroup, self).__init__(**kwargs)

        base_pulley = Pulley(
            radius=radius,
            color=color,
            stroke_width=stroke_width
        )
        self.base_pulley = base_pulley

        fixed_rod = Line(
            start=[0, radius * 1.5, 0],
            end=[0, radius * 1.5 + rod_length, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.fixed_rod = fixed_rod

        self.add(base_pulley, fixed_rod)

from __future__ import annotations

import math
import numpy as np
from manim import *


class Rope(VGroup):
    """绳子组件。"""

    def __init__(
        self,
        length: float = 4.0,
        angle: float = 0,
        color: str = GRAY,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES
        start_point = np.array([
            -length/2 * math.cos(angle_rad),
            -length/2 * math.sin(angle_rad),
            0
        ])
        end_point = np.array([
            length/2 * math.cos(angle_rad),
            length/2 * math.sin(angle_rad),
            0
        ])

        rope = Line(
            start=start_point,
            end=end_point,
            color=color,
            stroke_width=stroke_width
        )
        self.rope = rope

        self.add(rope)

from __future__ import annotations

from manim import *


class Spring(VGroup):
    """弹簧组件。"""

    def __init__(
        self,
        length: float = 4.0,
        height: float = 0.6,
        num_coils: int = 8,
        end_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        coil_width = (length - 2 * end_length) / num_coils

        left_end = Line(
            start=[-length/2, 0, 0],
            end=[-length/2 + end_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.left_end_line = left_end

        zigzag_points = [[-length/2 + end_length, 0, 0]]

        for i in range(num_coils):
            x_start = -length/2 + end_length + i * coil_width
            zigzag_points.append([x_start + coil_width/2, height/2, 0])
            zigzag_points.append([x_start + coil_width, -height/2, 0])

        zigzag_points.append([length/2 - end_length, 0, 0])

        zigzag = VMobject()
        zigzag.set_points_as_corners(zigzag_points)
        zigzag.set_color(color)
        zigzag.set_stroke(width=stroke_width)
        self.zigzag = zigzag

        right_end = Line(
            start=[length/2 - end_length, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.right_end_line = right_end

        self.add(left_end, zigzag, right_end)

from __future__ import annotations

from manim import *


class Rod(VGroup):
    """刚性杆组件。"""

    def __init__(
        self,
        length: float = 4.0,
        thickness: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        rod = Rectangle(
            width=length,
            height=thickness,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.rod = rod

        self.add(rod)

from __future__ import annotations

import math
import numpy as np
from manim import *


class Wall(VGroup):
    """墙面/地面组件，包含主线与阴影短线。"""

    def __init__(
        self,
        length: float = 8.0,
        angle: float = 0,
        rise_to: str = "right",
        hatch_spacing: float = 0.4,
        hatch_length: float = 0.25,
        contact_offset_y: float = 0.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_value = float(angle)
        rise_to_value = str(rise_to).strip().lower()
        if rise_to_value not in {"left", "right"}:
            raise ValueError("rise_to must be 'left' or 'right'")
        if angle_value < 0:
            angle_value = abs(angle_value)
            if rise_to_value == "right":
                rise_to_value = "left"
        if angle_value > 90:
            raise ValueError("Wall angle must be in [0, 90] degrees")

        main_line = Line(
            start=[-length/2, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        hatch_lines = VGroup()
        num_hatches = int(length / hatch_spacing)

        hatch_angle = -45 * DEGREES
        hatch_direction = np.array([
            math.cos(hatch_angle),
            math.sin(hatch_angle),
            0
        ])

        for i in range(num_hatches):
            x = -length/2 + i * hatch_spacing

            start_point = np.array([x, 0, 0])

            end_point = start_point + hatch_direction * hatch_length

            hatch = Line(
                start=start_point,
                end=end_point,
                color=color,
                stroke_width=stroke_width * 0.6
            )
            hatch_lines.add(hatch)

        self.add(main_line, hatch_lines)
        signed_angle = angle_value if rise_to_value == "right" else -angle_value
        if signed_angle != 0.0:
            self.rotate(signed_angle * DEGREES, about_point=ORIGIN)

        if float(contact_offset_y) != 0.0:
            self.shift(UP * float(contact_offset_y))
