# 布局契约执行规范（LLM4）

输入中的 `scene_designs.scenes[*].layout_contract` 是硬约束。  
你必须按契约生成代码，而不是仅参考自然语言布局描述。

## 必须执行

1) 解析 `layout_contract.zones`：建立标题区/主图区/公式区/总结区。  
2) 解析 `layout_contract.objects`：每个对象按 `zone` 放置，并遵守 `max_width_ratio`。  
3) 解析 `layout_contract.step_visibility`：按步显示/隐藏对象，避免叠屏。  
4) 执行 `global_rules.avoid_overlap=true`：使用包围盒检测避免重叠。  
5) 执行 `global_rules.formula_stack=arrange_down`：多条公式必须分组竖排。  
6) 执行 `global_rules.text_language`：自然语言文本默认中文（符号标签除外）。

## 推荐实现模式

```python
# 1) 分区锚点（可按场景尺寸换算）
title_anchor = UP * 3.1
formula_anchor = RIGHT * 4.2 + UP * 1.8
summary_anchor = DOWN * 3.2

# 2) 公式组统一排版，避免硬编码堆叠
formula_group = VGroup(eq1, eq2, eq3).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
formula_group.move_to(formula_anchor)

# 3) 超宽对象自动缩放
if formula_group.width > config.frame_width * 0.30:
    formula_group.scale_to_fit_width(config.frame_width * 0.30)
```

## 防重叠最低要求

1) 不允许出现“同一帧中两条公式互相覆盖”。  
2) 不允许标题与公式覆盖。  
3) 不允许总结文字覆盖主图关键对象。  
4) 若对象过多：优先拆到下一步，不要同帧硬塞。

## 与 motion_constraints 协同

- 布局契约只管“放置与显隐”；  
- 运动约束只管“轨迹与锚点命中”；  
- 代码中必须同时满足两者。
