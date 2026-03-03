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
