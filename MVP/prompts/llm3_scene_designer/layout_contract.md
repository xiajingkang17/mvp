# 布局契约（layout_contract v1）

你必须输出 `layout_contract`，用于把布局描述升级为可执行约束。

## 目标

1. 防止文字、公式、主图重叠。
2. 防止对象越界。
3. 给 LLM4 提供可直接编译的布局规则。
4. 让布局意图在 step 间保持稳定。

## 必须输出的结构

```json
{
  "layout_contract": {
    "version": "v1",
    "language": "zh-CN",
    "safe_margin": 0.04,
    "zones": [
      {"id": "title_zone", "role": "title", "x0": 0.05, "y0": 0.88, "x1": 0.95, "y1": 0.98},
      {"id": "main_zone", "role": "main", "x0": 0.05, "y0": 0.16, "x1": 0.62, "y1": 0.86},
      {"id": "formula_zone", "role": "formula", "x0": 0.65, "y0": 0.20, "x1": 0.95, "y1": 0.86},
      {"id": "subtitle_zone", "role": "subtitle", "x0": 0.05, "y0": 0.02, "x1": 0.95, "y1": 0.12}
    ],
    "global_rules": {
      "avoid_overlap": true,
      "min_gap": 0.02,
      "formula_stack": "arrange_down",
      "subtitle_reserved": true
    },
    "objects": [
      {"id": "title_1", "kind": "text", "zone": "title_zone", "priority": 100},
      {"id": "eq_main", "kind": "math", "zone": "formula_zone", "priority": 80, "max_width_ratio": 0.92}
    ],
    "step_visibility": [
      {"step": 1, "layout_objects": ["title_1"], "zone_overrides": {}}
    ]
  }
}
```

## 规则

1. `zones` 使用 0~1 归一化坐标。
2. 每个 zone 必须包含 `role`。
3. `step_visibility` 只描述该 step 参与布局计算的对象，不表达 show/hide/remove。
4. `subtitle` zone 如果存在，必须位于底部，并保持为保留区。
5. `steps[*].narration` 只有在存在 `subtitle` zone 时才映射到该区域。
6. `on_screen_text` 不能占用 `subtitle` zone；如果你需要额外文字说明，请使用 `title`、`summary`、`aux` 等其他 role，不要额外发明第二个字幕区。

## 与生命周期的边界

- 谁出现、谁消失，只看 `steps[*].object_ops`。
- scene 结束谁保留，只看 `exit_state.objects_on_screen`。
- `layout_contract` 不承担生命周期职责。

## 字幕硬规则

下面这些规则是强制的，优先级高于任何柔性布局偏好：

1. 每个 scene 最多只能有一个字幕区；如果存在，归一化坐标固定为：
   - `x0 = 0.05`
   - `x1 = 0.95`
   - `y0 = 0.02`
   - `y1 = 0.12`
2. 如果 scene 不需要字幕，可以完全不输出 `subtitle` zone。
3. 一旦输出了字幕区，它在整幕中不可变。不要改尺寸、不要移动、不要在 step 级覆写。
4. 字幕区是保留区，不是剩余空间。任何 `main`、`formula`、`summary`、`title`、`aux` zone 都不能与它重叠。
5. `layout_contract.objects` 不允许把任何常驻屏幕对象放进字幕区；只有运行时字幕文本可以出现在这里。
6. 如果某个 step 的 narration 在正常可读字号下放不进固定字幕区，就拆 step 或缩短 narration；不要压缩字幕区，也不要依赖极小字号。
