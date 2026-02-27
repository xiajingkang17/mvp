# 运行时规则

1. builder 函数签名：`(spec: dict[str, Any]) -> Mobject`。
2. updater 函数签名：`(mobj: Mobject, t: float, spec: dict[str, Any]) -> None`。
3. builder 返回值必须是 Manim `Mobject`（如 `VGroup`、`Circle`、`Dot`）。
4. updater 应只修改传入对象，不创建外部状态依赖。
5. 代码需兼容 Python 3.10+，避免项目外部依赖。

## DSL 读取规范（强制）

1. 先拆分 DSL：
   - `geom = dict(spec.get("geometry", {}) or {})`
   - `style = dict(spec.get("style", {}) or {})`
   - `motion = dict(spec.get("motion", {}) or {})`
   - `effects = dict(spec.get("effects", {}) or {})`
   - `meta = dict(spec.get("meta", {}) or {})`
2. 不要把 `spec` 顶层当成自由参数字典直接硬编码读取。

## 文本与 LaTeX 渲染规则（强制）

1. 纯中文或纯自然语言文本：使用 `Text()`。
2. 纯数学公式：使用 `MathTex()`，并使用原始字符串（如 `r"\\frac{a}{b}"`）。
3. 混合内容（中文 + 公式）：拆分渲染后用 `VGroup()` 组合，不要把整段混合文本直接塞进 `MathTex()`。
4. 不要把 LaTeX 命令放进 `Text()`；不要把中文段落放进 `MathTex()`。

## 视觉质量规则（强制）

1. 颜色优先从 `style.palette` 与 `style.color_map` 读取，保持变量/元素颜色一致。
2. 给主要对象设置清晰层级（如 `set_z_index`），避免文字被遮挡。
3. 布局要显式控制间距与对齐（`arrange`、`next_to`、`to_edge`），避免重叠堆叠。
4. 线宽、透明度、字号要有默认值且可由 `style.sizes` 覆盖。
5. 避免“超大/超小”对象：关键尺寸请做合理 clamp。

## 动画与时序规则（强制）

1. `t` 表示本对象局部时间，动画参数应可随 `t` 连续变化。
2. 若使用 `motion_span_s` 或阶段时长，需防除零并做边界裁剪（例如 clamp 到 `[0,1]`）。
3. 禁止离散跳变造成明显闪烁或瞬移（除非语义明确要求）。

## 箭头 API 规则（强制）

1. 优先使用稳定高层 API：
   - `Arrow(start, end, ...)`
   - `CurvedArrow(start_point=..., end_point=..., ...)`
   - `Line(...).add_tip()`
2. 禁止直接实例化 `ArrowTip(...)`（抽象基类，运行时会报错）。
3. 禁止 `CubicBezier(...).add_tip(...)`（`CubicBezier` 不支持该方法）。
4. 若需要“曲线 + 箭头头”，优先改用 `CurvedArrow`，不要手工拼接抽象 tip。

## 上下文边界

1. builder/updater 中没有 `Scene` 上下文，不要访问 `self` 或 `camera.frame`。
2. 仅构建/更新对象本身，不控制全局场景流程。
