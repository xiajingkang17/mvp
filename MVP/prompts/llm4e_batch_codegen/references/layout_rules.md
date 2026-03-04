# 布局规则

## 布局来源优先级

1. 布局优先服从 `scene_layout.layout_contract`
2. 其次参考 `scene_layout.layout_prompt`
3. `scene_design` 中残留的布局信息只作为补充，不要覆盖 `llm35` 已经明确给出的布局合同
4. 不要忽略 `llm35` 给出的布局合同后自己重新摆一套

## 当前架构中的布局合同

`llm35` 输出的布局核心是：

1. `layout_prompt`
   对这一幕画面组织的自然语言描述
2. `layout_contract.zones`
   场景骨架，每个 zone 都是精确坐标
3. `layout_contract.objects`
   对象组进入哪个 zone、采用什么锚点与宽高约束
4. `layout_contract.step_layouts`
   当前 step 相对场景骨架的增量布局变化

`llm4e` 的职责不是重新设计布局，而是把这些信息翻译成代码。

## zone 使用规则

1. 不要只拿到 zone 后把对象都 `move_to(zone center)`
2. 优先使用：
   - `make_wrapped_text_block(...)`
   - `place_in_zone_anchor(...)`
   - `fit_in_zone(...)`
   - `VGroup(...).arrange(...)`
3. `zones` 是骨架，不是最终对象坐标
4. 对象进入 zone 后，还要继续落实 `anchor`、`align`、`max_width_ratio`、`max_height_ratio`

## 对象组执行规则

1. 长文本组：
   - 题干
   - 条件块
   - 分问列表
   - 问题卡
   - 总结块
   这些优先走 `make_wrapped_text_block(...)`
2. 题干组、问题卡、总结块优先贴 `top_left` 或 `left`
3. 主图组优先整体居中或偏一侧，不要侵入字幕区和题干区
4. 公式组优先纵向排列，不要与主图中心重叠
5. 标签组优先相对主图锚点摆放，不要凭感觉压在主图中心

## step 增量布局规则

1. `step_layouts` 用来描述当前 step 相对 scene 骨架的局部变化
2. 不要把每个 step 都重新发明一套完整布局
3. 常见变化包括：
   - 当前问题卡移到左上角
   - 主图缩小并让出公式区
   - 某些对象组隐藏
   - 某些对象组改到新的 zone
4. scene 级骨架保持稳定，step 级只做增量调整

## 避免重叠

1. 题干组、主图组、公式组默认不能压在同一个中心区域
2. 字幕区是固定保留区，不允许任何对象占用
3. 长文本块进入 zone 前，先考虑宽度与换行，再考虑字号缩放
4. 如果 `layout_contract.objects` 和 `step_layouts` 已经给出不同 zone，必须执行这种分离，不要重新合并到同一块区域

## 常见错误

1. 只定义 `zone_main`，然后把题干、主图、公式都摆进去
2. 长题干直接 `Text(long_text).move_to(...)`
3. 有了 `step_layouts` 还完全不理会，导致每一步的对象都压在一起
4. 主图、公式、说明文字全部围绕同一个中心点摆放
