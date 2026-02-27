# 叙事分镜规则（必须遵守）

为每个 scene 生成 `narrative_storyboard`，结构至少包含：

1. `bridge_from_prev`：与上一个概念的衔接语（首幕可为空）。
2. `intro`：自然引入本幕概念。
3. `key_formulae[]`：关键公式列表。每项使用：
   - `latex`（必填）
   - `color`（可选）
   - `position_hint`（可选）
   - `duration_s`（可选，>0）
   禁止使用未定义字段（例如 `position`）。
4. `animation_steps[]`：按顺序描述每一步动画，必须写清：
   - `id`（必填，步骤唯一标识，如 `step_1`）
   - `description`（这一步做什么，必须是完整描述）
   - `targets`（必填，涉及对象，非空）
   - `duration_s`（必填，时长，>0）
   - `color_hint`（可选，颜色强调）
   - `position_hint`（可选，位置意图）
5. `bridge_to_next`：非最终幕必须给出到下一概念的铺垫语。

附加要求：

1. 分镜描述必须可执行，避免泛化叙述。
2. 公式应与本幕目标直接相关，避免堆砌。
3. `animation_steps[].id` 在同一 scene 内必须唯一。
4. 步骤数量建议 4-7 步；极简场景可 3 步，但必须保证起承转合完整。
5. `animation_steps[].description` 应明确动作原语，优先使用：`FadeIn`、`FadeOut`、`Create`、`Write`、`Transform`。
6. 每个步骤描述应包含：对象、动作、位置或构图变化、运动方向/路径、起止状态、教学意图，不要只写一句短词。
7. `bridge_from_prev`、`intro`、`bridge_to_next` 都应写成自然衔接段落，而非口号式短句。
8. 动画链路应尽量覆盖：几何基底建立 -> 关键关系显化 -> 公式/结论呈现 -> 过渡或收束。
