# 历史错误案例 002：`VGroup(*self.mobjects)` 触发类型错误

## 真实报错（已发生）

- 典型位置：`self.play(FadeOut(VGroup(*self.mobjects)))`
- 典型异常：
  `TypeError: Only values of type VMobject can be added as submobjects of VGroup`

## 根因

- `VGroup` 只能容纳 `VMobject`。
- `self.mobjects` 是当前场景全部对象的混合列表，可能包含普通 `Mobject`。
- 把 `self.mobjects` 直接塞进 `VGroup` 会在运行时报类型错误。

## 生成硬约束（必须遵守）

1) 禁止使用 `VGroup(*self.mobjects)`。
2) 需要整体淡出全场对象时，优先使用以下任一安全方案：
   - `Group(*self.mobjects)`（允许混合 `Mobject`）
   - `self.play(*[FadeOut(m) for m in list(self.mobjects)])`
3) 只有在你明确确认对象全为 `VMobject` 时，才允许使用 `VGroup(...)`。

## 推荐安全写法

```python
# 方案 A：Group
self.play(FadeOut(Group(*self.mobjects)))

# 方案 B：逐个 FadeOut（更稳）
self.play(*[FadeOut(m) for m in list(self.mobjects)])
```

## 输出前自检清单（必须执行）

- 代码中是否出现 `VGroup(*self.mobjects)`？若有必须替换。
- 所有 `VGroup(...)` 的入参是否都可确认为 `VMobject`？
