# 布局契约（layout_contract v1）

你必须在输出 JSON 顶层提供 `layout_contract` 字段，用于把“布局描述”升级为“可执行约束”。

## 目标

1) 防止文本/公式重叠  
2) 防止对象越界  
3) 明确每一步对象的出现与消失（生命周期）  
4) 为 LLM4 提供可直接落地的布局规则

## 必须输出的结构

```json
{
  "layout_contract": {
    "version": "v1",
    "language": "zh-CN",
    "safe_margin": 0.4,
    "zones": [
      {"id": "title_zone", "x0": 0.05, "y0": 0.88, "x1": 0.95, "y1": 0.98},
      {"id": "main_zone", "x0": 0.05, "y0": 0.15, "x1": 0.62, "y1": 0.86},
      {"id": "formula_zone", "x0": 0.65, "y0": 0.20, "x1": 0.95, "y1": 0.86},
      {"id": "summary_zone", "x0": 0.05, "y0": 0.03, "x1": 0.95, "y1": 0.13}
    ],
    "global_rules": {
      "avoid_overlap": true,
      "min_gap": 0.18,
      "formula_stack": "arrange_down",
      "max_formula_width_ratio": 0.30,
      "overflow_policy": ["shrink", "move_down", "split_next_step"],
      "text_language": "chinese_only_except_symbols"
    },
    "objects": [
      {
        "id": "title_1",
        "kind": "text",
        "zone": "title_zone",
        "priority": 100,
        "max_width_ratio": 0.85
      },
      {
        "id": "eq_main",
        "kind": "math",
        "zone": "formula_zone",
        "priority": 80,
        "max_width_ratio": 0.30
      }
    ],
    "step_visibility": [
      {"step": 1, "show": ["title_1"], "hide": []},
      {"step": 2, "show": ["eq_main"], "hide": []}
    ]
  }
}
```

## 约束说明

1) `zones` 使用归一化坐标（0~1）描述画面分区。  
2) `objects` 中每个对象都要绑定 `zone`。  
3) 公式对象必须有 `max_width_ratio`，防止长公式越界。  
4) `step_visibility` 必须覆盖关键对象，避免旧元素残留堆叠。  
5) 文案默认中文；符号标签可保留 `L1/L2/L3/L4/P/Q/E/B_1/B_2/v_0`。

## 与 motion_constraints 的关系

- `layout_contract` 负责“放哪里、何时显示”。  
- `motion_constraints` 负责“怎么动、到哪里结束”。  
- 两者都必须输出，且不冲突。
