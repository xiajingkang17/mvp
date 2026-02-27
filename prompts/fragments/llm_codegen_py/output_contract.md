# 输出合同

1. 只输出完整 Python 代码，不要 Markdown。
2. 必须定义：
   - `BUILDERS: dict[str, callable]`
3. 可选定义：
   - `UPDATERS: dict[str, callable]`
4. `BUILDERS` 必须覆盖输入 manifest 中所有 `code_key`。
5. builder/updater 接收的 `spec` 来自 DSL：
   - `spec["geometry"]`
   - `spec["style"]`
   - `spec["motion"]`
   - `spec["effects"]`
   - `spec["meta"]`

## 代码级硬约束

1. 不输出运行命令，不输出额外说明文字。
2. 代码需可直接被 `importlib` 导入。
3. 所有 `BUILDERS[code_key]` 必须可调用，且返回 `Mobject`。
4. 若定义 `UPDATERS`，其函数必须可调用并且签名可兼容 `(mobj, t, spec)`。

## 输出前自检（内部执行，不要输出此清单）

1. LaTeX 字符串是否可被 `MathTex` 正常解析。
2. 是否存在未定义变量或拼写错误。
3. 是否存在明显语法错误（括号、引号、缩进）。
4. 是否错误混用文本与公式渲染类。
5. 箭头实现是否使用受支持 API（禁止 `ArrowTip(...)` 与 `CubicBezier(...).add_tip(...)`）。
