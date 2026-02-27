# 约束与 LLM 联动改造清单（待办）

## 目标

- 让 LLM 稳定产出可执行、几何一致的约束描述。
- 减少“坐标写错、内外侧写反、轨道不一致”等问题。

## 当前现状

- 已有约束：`attach`、`midpoint`、`align_axis`、`distance`、`align_angle`、`on_track_pose`。
- 轨道主约束已统一为 `on_track_pose`（位置 + 姿态）。
- 圆弧内外侧判定已采用径向规则（不依赖切线方向）。

## 后续必须做（LLM 接入前）

1. `run_llm2` 约束强校验

- 若 `constraint.type=on_track_pose` 且目标轨道为 `arc`，强制要求 `args.contact_side` 存在且合法。
- 非法值直接报错并触发修复轮。

1. `validate_plan` / repair 自动修复

- 对缺失 `contact_side` 的圆弧轨道约束给出自动补全策略（默认值 + warning）。
- 在修复日志中明确标记补全位置，便于复核。

1. Prompt 与 few-shot 更新

- 在 LLM2 提示词中加入“轨道接触统一用 `on_track_pose`，圆弧必须显式写 `contact_side`”硬规则。
- 增加标准示例：
  - 斜面接触（`on_track_pose`）
  - 圆弧接触（`on_track_pose` + `contact_side`）

1. 轨道生成规范

- 优先从图元几何提取轨道，而非手填绝对坐标。
- 手填坐标仅作为最后手段。

1. 接触细节参数规范

- 约定场景常量：`DEFAULT_CONTACT_SIDE`、`DEFAULT_CLEARANCE`、`USE_AUTO_CLEARANCE`。
- 对圆弧场景强制显式 `contact_side`。

## 中期建议

1. 组件语义锚点

- 为关键组件补语义锚点/语义边（例如 `InclinedPlane.slope`）。
- `anchors.py` 优先读取组件显式锚点，缺失再回退 bbox 锚点。

1. 轨道语义引用

- 支持 `track_ref`（例如 `part_id + edge_name`），减少 LLM 直接输出坐标。

1. 姿态连续性增强

- 增加角度解包（unwrap）和角速度限制，减少折点处翻转感。
