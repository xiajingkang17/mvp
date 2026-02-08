# 电学组件库 - 简单使用说明

## 📚 概述

这是一个**纯静态**的电学组件库，专注于简单的可视化展示。不包含复杂的物理计算或运动逻辑。

## 🎯 设计原则

✅ **简单至上** - 只画形状，不做计算
✅ **清晰直观** - 线条清晰，颜色醒目
✅ **易于使用** - 继承自 VGroup，可直接使用 Manim 方法

## 📦 组件列表

### 1. Resistor (电阻)
- **形状**: 锯齿状折线
- **参数**: `width`, `height`, `color`, `stroke_width`
- **用途**: 表示电阻元件

### 2. Battery (电池)
- **形状**: 长线（正极）+ 短线（负极）
- **参数**: `width`, `height_long`, `height_short`, `show_labels`
- **特点**: 自动标记 + 和 -

### 3. Bulb (灯泡)
- **形状**: 圆圈 + 交叉线（X）
- **参数**: `radius`, `fill_color`, `fill_opacity`
- **特点**: 可设置填充颜色和透明度

### 4. Switch (开关)
- **形状**: 断开的闸刀式结构
- **参数**: `width`, `height`
- **状态**: 默认断开状态

### 5. Capacitor (电容) - 额外赠送
- **形状**: 两条平行竖线
- **参数**: `width`, `height`

## 🚀 快速开始

### 基本使用

```python
from manim import *
from components.physics.electricity import Resistor, Battery, Bulb, Switch

class MyScene(Scene):
    def construct(self):
        # 创建组件（使用默认参数）
        resistor = Resistor()
        battery = Battery()
        bulb = Bulb()
        switch = Switch()

        # 排列显示
        components = VGroup(resistor, battery, bulb, switch)
        components.arrange(RIGHT, buff=1.5)
        components.center()

        # 添加到场景
        self.add(components)
```

### 自定义样式

```python
# 创建大尺寸、红色电阻
resistor = Resistor(
    width=4.0,        # 更宽
    height=1.0,       # 更高
    color=RED,        # 红色
    stroke_width=6.0  # 更粗的线条
)

# 创建带标签的电池
battery = Battery(
    height_long=1.5,
    height_short=0.8,
    show_labels=True  # 显示 + 和 -
)

# 创建黄色灯泡
bulb = Bulb(
    radius=0.8,
    fill_color=YELLOW,
    fill_opacity=0.5  # 半透明
)
```

## 🎬 运行测试

### 快速测试（简单展示）
```bash
python3.11 -m manim -pql cases/physics_demo/test_electricity.py TestSimpleShowcase
```

### 完整展示（带动画）
```bash
python3.11 -m manim -pql cases/physics_demo/test_electricity.py TestElectricityComponents
```

### 单个组件示例
```bash
python3.11 -m manim -pql cases/physics_demo/test_electricity.py TestSingleComponent
```

## 📂 文件位置

```
mvp-main/
├── components/
│   └── physics/
│       └── electricity.py          ⭐ 核心组件代码
└── cases/
    └── physics_demo/
        ├── test_electricity.py     ⭐ 测试场景
        └── README_ELECTRICITY.md   📖 本文档
```

## 🎨 代码示例

### 示例 1：创建组件展示柜

```python
from components.physics.electricity import *

class Showcase(Scene):
    def construct(self):
        # 创建4个组件
        r = Resistor()
        b = Battery()
        l = Bulb()
        s = Switch()

        # 添加文字标签
        labels = VGroup(
            Text("Resistor"),
            Text("Battery"),
            Text("Bulb"),
            Text("Switch")
        )

        # 组合组件和标签
        groups = [
            VGroup(r, labels[0]).arrange(DOWN),
            VGroup(b, labels[1]).arrange(DOWN),
            VGroup(l, labels[2]).arrange(DOWN),
            VGroup(s, labels[3]).arrange(DOWN)
        ]

        # 一字排开
        showcase = VGroup(*groups)
        showcase.arrange(RIGHT, buff=1.0)
        self.add(showcase)
```

### 示例 2：自定义颜色和大小

```python
class Colorful(Scene):
    def construct(self):
        # 不同颜色的组件
        resistor = Resistor(color=RED, stroke_width=5)
        battery = Battery(color=BLUE, stroke_width=5)
        bulb = Bulb(fill_color=YELLOW, fill_opacity=0.5)
        switch = Switch(color=GREEN, stroke_width=5)

        components = VGroup(resistor, battery, bulb, switch)
        components.arrange(RIGHT, buff=1.5)
        self.add(components)
```

### 示例 3：带动画展示

```python
class Animated(Scene):
    def construct(self):
        resistor = Resistor()
        battery = Battery()
        bulb = Bulb()

        # 水平排列
        components = VGroup(resistor, battery, bulb)
        components.arrange(RIGHT, buff=2.0)

        # 依次显示
        self.play(Create(resistor))
        self.wait(0.5)
        self.play(Create(battery))
        self.wait(0.5)
        self.play(Create(bulb))
        self.wait(2)
```

## 📊 参数说明

### Resistor 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width` | float | 3.0 | 总宽度 |
| `height` | float | 0.8 | 锯齿高度 |
| `color` | str | WHITE | 线条颜色 |
| `stroke_width` | float | 4.0 | 线条宽度 |

### Battery 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width` | float | 1.5 | 极板间距 |
| `height_long` | float | 1.2 | 正极长度 |
| `height_short` | float | 0.6 | 负极长度 |
| `show_labels` | bool | True | 是否显示 +/- |

### Bulb 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `radius` | float | 0.6 | 圆圈半径 |
| `fill_color` | str | YELLOW | 填充颜色 |
| `fill_opacity` | float | 0.3 | 填充透明度 |

### Switch 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width` | float | 2.0 | 总宽度 |
| `height` | float | 0.8 | 闸刀抬起高度 |

## 💡 使用技巧

1. **调整大小**: 使用 `.scale()` 方法
   ```python
   resistor.scale(1.5)  # 放大1.5倍
   ```

2. **移动位置**: 使用 `.shift()` 或 `.move_to()`
   ```python
   battery.shift(UP * 2)
   bulb.move_to([0, 0, 0])
   ```

3. **旋转**: 使用 `.rotate()`
   ```python
   resistor.rotate(90 * DEGREES)
   ```

4. **组合**: 使用 VGroup 组合多个组件
   ```python
   circuit = VGroup(resistor, battery, bulb)
   ```

## 🎓 学习要点

- 所有组件都是 `VGroup` 的子类
- 使用简单的几何图形组合而成（Line, Circle, VMobject等）
- 不涉及复杂的物理计算
- 易于理解和扩展

## 📝 代码特点

- **简洁**: 每个组件约 30-60 行代码
- **清晰**: 详细的中文注释
- **独立**: 组件之间无依赖关系
- **灵活**: 参数化设计，易于自定义

## 🎯 下一步

1. 尝试修改参数，观察效果
2. 创建自己的组合电路
3. 添加更多电学元件（电感、二极管等）
4. 为组件添加更多样式选项

---

**简单就是美！** ✨
