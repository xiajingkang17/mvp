# 文本与公式规则

1. 自然语言使用 `TextBlock.params.text`。
2. 在 `TextBlock.params.text` 中，任何 LaTeX 公式片段必须用 `$...$` 包裹。
3. `$...$` 外是普通文本（中文、英文、标点）；`$...$` 内是公式。
4. 仅当对象是“纯公式”时，才使用 `Formula.params.latex`。
5. `Formula.params.latex` 不要包含中文句子。
6. 公式字符串必须是 Manim 兼容 LaTeX；在 JSON 中反斜杠需正确转义（例如 `\\frac{1}{2}mv^2`）。
