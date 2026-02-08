# 物理力学组件库 - 快速参考

## 🚀 30秒快速上手

```python
from manim import *
from components.physics.mechanics_full import *

class Demo(Scene):
    def construct(self):
        block = Block()  # 创建滑块
        self.add(block)
```

## 📋 组件速查表

### 1️⃣ 基础环境 (2个)
```python
Wall(length=8.0, angle=0)              # 墙面/地面
InclinedPlane(angle=30, length=5.0)    # 斜面（带θ标注）
```

### 2️⃣ 刚体与物体 (3个)
```python
Block(width=1.5, height=1.0, label="m")    # 滑块
Cart(width=2.5, height=0.8)                # 小车
Weight(width=1.0, height=1.5)              # 钩码
```

### 3️⃣ 连接装置 (7个)
```python
Pulley(radius=0.5)                # 滑轮（基类）
FixedPulley(radius=0.5)           # 定滑轮
MovablePulley(radius=0.5)         # 动滑轮
Rope(length=4.0, angle=0)         # 绳
Spring(length=4.0)                # 弹簧（锯齿状）
Rod(length=4.0, angle=0)          # 杆
Hinge(size=0.6)                   # 铰链
```

### 4️⃣ 轨道与槽车 (5个)
```python
CircularGroove(radius=2.0)                   # 圆槽
SemicircleGroove(radius=2.0)                 # 半圆槽
QuarterCircleGroove(radius=2.0)              # 1/4圆槽
SemicircleCart(width=3.0)                    # 半圆槽车
QuarterCart(width=3.0, groove_side="left")   # 1/4圆槽车
```

### 5️⃣ 测量工具 (1个)
```python
SpringScale(width=1.0, height=3.0)   # 弹簧测力器
```

## 🎯 常用组合示例

### 斜面滑块
```python
plane = InclinedPlane(angle=30)
block = Block()
block.rotate(30 * DEGREES)
self.add(plane, block)
```

### 滑轮组
```python
fixed = FixedPulley().shift(UP * 2)
movable = MovablePulley().shift(DOWN)
rope = Rope(length=4, angle=90)
self.add(fixed, movable, rope)
```

### 小车与弹簧
```python
cart = Cart().shift(LEFT * 2)
spring = Spring().shift(RIGHT * 0.5)
wall = Wall(angle=90).shift(RIGHT * 3)
self.add(cart, spring, wall)
```

## 🎨 常用变换

```python
component.scale(1.5)                    # 缩放
component.rotate(45 * DEGREES)          # 旋转
component.shift(UP * 2)                 # 移动
component.center()                      # 居中
component.to_edge(UP)                   # 移到边缘
```

## 🔧 自定义样式

```python
# 改变颜色
block = Block(color=RED, stroke_width=6)

# 调整尺寸
cart = Cart(width=3.0, height=1.0)

# 自定义标签
block = Block(label="m1", label_color=YELLOW)
```

## 📦 完整导入

```python
from components.physics.mechanics_full import (
    Wall, InclinedPlane,
    Block, Cart, Weight,
    Pulley, FixedPulley, MovablePulley,
    Rope, Spring, Rod, Hinge,
    CircularGroove, SemicircleGroove, QuarterCircleGroove,
    SemicircleCart, QuarterCart,
    SpringScale
)
```

## 🎬 运行测试

```bash
# 快速展示（所有18种组件）
python3.11 -m manim -pql cases/physics_test/test_mechanics_full.py TestQuickShowcase

# 完整展示（4行5列网格）
python3.11 -m manim -pql cases/physics_test/test_mechanics_full.py TestMechanicsFull

# 按类别展示
python3.11 -m manim -pql cases/physics_test/test_mechanics_full.py TestByCategory
```

## 📊 组件统计

| 类别 | 数量 | 组件 |
|------|------|------|
| 基础环境 | 2 | Wall, InclinedPlane |
| 刚体与物体 | 3 | Block, Cart, Weight |
| 连接装置 | 7 | Pulley, FixedPulley, MovablePulley, Rope, Spring, Rod, Hinge |
| 轨道与槽车 | 5 | CircularGroove, SemicircleGroove, QuarterCircleGroove, SemicircleCart, QuarterCart |
| 测量工具 | 1 | SpringScale |
| **总计** | **18** | |

---

**快速、简单、完整！** ⚡
