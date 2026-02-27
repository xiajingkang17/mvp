# 历史错误案例 001：`NameError: name 'arc1' is not defined`

## 真实报错（已发生）

- 典型位置：`self.play(arc1.animate.set_color(GRAY), ...)`
- 典型异常：`NameError: name 'arc1' is not defined`

## 根因

- 在某个函数里把 `arc1/arc2/arc3` 作为局部变量创建。
- 在另一个函数（或后续 scene）里直接引用这些变量名。
- 局部变量作用域已结束，导致运行时找不到变量。

## 生成硬约束（必须遵守）

1) 任何需要跨 `step` 或跨函数复用的对象，必须用 `self.<name>` 保存与访问。
2) `construct()` 开头先初始化跨函数对象（例如 `self.arc1 = None`）。
3) 在任意函数中，禁止直接使用未在本函数定义且未加 `self.` 的裸变量名（如 `arc1`）。
4) 在 `self.play(...)` 中出现的每个对象，必须保证在当前可见作用域中已定义。

## 正确写法示例

```python
# 在创建处
self.arc1 = Arc(...)

# 在后续函数中复用
if self.arc1 is not None:
    self.play(self.arc1.animate.set_color(GRAY))
```

## 输出前自检清单（必须执行）

- 是否存在 `self.play(arc1...`、`self.play(arc2...` 这类裸变量调用？
- 是否所有跨函数复用对象都改成了 `self.xxx`？
- 是否在 `construct()` 中完成了跨函数对象初始化？
