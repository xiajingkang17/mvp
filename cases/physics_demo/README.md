# 斜面滑块受力分析组件 - 使用说明

## 📚 概述

`InclinedPlaneGroup` 是一个完整的物理力学可视化组件，用于演示滑块在斜面上的受力分析。

## 🎯 组件功能

### 核心特性
- ✅ **参数化设计**：可以自定义斜面角度、尺寸、滑块大小
- ✅ **完整的受力分析**：重力(mg)、支持力(F_N)、摩擦力(f)
- ✅ **颜色区分**：每个力使用不同颜色（红、蓝、绿）
- ✅ **LaTeX 标签**：专业的数学符号标注
- ✅ **角度标注**：自动显示斜面角度 θ
- ✅ **可动画化**：支持滑块滑动、力箭头显示等动画

## 📁 文件结构

```
components/physics/
├── __init__.py              # 模块初始化
├── mechanics.py             # ⭐ 核心组件代码
├── inclined_plane.py        # 占位文件
├── block.py                 # 占位文件
└── force_vector.py          # 占位文件

cases/physics_demo/
├── test_mechanics.py        # ⭐ 测试场景代码
└── README.md                # 本文档
```

## 🚀 快速开始

### 1. 导入组件

```python
from components.physics.mechanics import InclinedPlaneGroup
```

### 2. 基本使用

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # 创建斜面组件
        plane = InclinedPlaneGroup(
            angle=30,           # 斜面角度（度）
            length=5.0,         # 底边长度
            block_width=1.0,    # 滑块宽度
            block_height=0.6,   # 滑块高度
            show_forces=True,   # 显示受力分析
            show_angle=True     # 显示角度标注
        )

        # 居中显示
        plane.center()

        # 添加到场景
        self.add(plane)
```

## 🎨 参数详解

### InclinedPlaneGroup 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `angle` | float | 30 | 斜面角度（度数）|
| `length` | float | 5.0 | 斜面底边长度 |
| `block_width` | float | 1.0 | 滑块宽度 |
| `block_height` | float | 0.6 | 滑块高度 |
| `show_forces` | bool | True | 是否显示受力分析箭头 |
| `show_angle` | bool | True | 是否显示角度标注 |

### 力向量说明

| 力 | 颜色 | 方向 | 标签 |
|----|------|------|------|
| 重力 | 红色 (RED) | 竖直向下 | mg |
| 支持力 | 蓝色 (BLUE) | 垂直斜面向上 | F_N |
| 摩擦力 | 绿色 (GREEN) | 沿斜面向上 | f |

## 📝 代码示例

### 示例 1：简单的斜面演示

```python
class SimpleDemo(Scene):
    def construct(self):
        # 创建30度斜面
        plane = InclinedPlaneGroup(angle=30)

        # 居中并显示
        plane.center()
        self.play(Create(plane), run_time=2)
```

### 示例 2：依次显示各个力

```python
class ShowForces(Scene):
    def construct(self):
        # 创建不显示力的斜面
        plane = InclinedPlaneGroup(
            angle=30,
            show_forces=False
        )
        plane.center()

        # 先显示斜面和滑块
        self.play(Create(plane))

        # 创建力向量
        gravity = plane.gravity
        normal = plane.normal_force
        friction = plane.friction

        # 依次显示
        self.play(Create(gravity))      # 重力
        self.wait(0.5)
        self.play(Create(normal))       # 支持力
        self.wait(0.5)
        self.play(Create(friction))     # 摩擦力
```

### 示例 3：滑块滑动动画

```python
class SlidingBlock(Scene):
    def construct(self):
        import math
        import numpy as np

        plane = InclinedPlaneGroup(angle=30)
        plane.center()

        self.play(Create(plane))

        # 计算滑动方向
        angle_rad = 30 * DEGREES
        slide_dir = np.array([
            math.cos(angle_rad),
            math.sin(angle_rad),
            0
        ])

        # 让滑块沿斜面下滑
        block = plane.block
        self.play(
            block.animate.shift(slide_dir * 0.8),
            run_time=2
        )
```

### 示例 4：对比不同角度

```python
class CompareAngles(Scene):
    def construct(self):
        # 创建三个不同角度的斜面
        plane1 = InclinedPlaneGroup(angle=15, length=3)
        plane2 = InclinedPlaneGroup(angle=30, length=3)
        plane3 = InclinedPlaneGroup(angle=45, length=3)

        # 排列显示
        plane1.shift(LEFT * 4)
        plane2.shift(LEFT * 0.5)
        plane3.shift(RIGHT * 3.5)

        self.play(
            Create(plane1),
            Create(plane2),
            Create(plane3)
        )
```

## 🎬 运行测试

### 运行简单测试（快速验证）
```bash
python3.11 -m manim -pql cases/physics_demo/test_mechanics.py TestSimple
```

### 运行完整演示
```bash
python3.11 -m manim -pql cases/physics_demo/test_mechanics.py TestInclinedPlane
```

### 运行角度对比
```bash
python3.11 -m manim -pql cases/physics_demo/test_mechanics.py TestDifferentAngles
```

### 渲染高质量视频
```bash
python3.11 -m manim -pqh cases/physics_demo/test_mechanics.py TestInclinedPlane
```

## 🎓 学习要点

### 1. VGroup 的使用
`InclinedPlaneGroup` 继承自 `VGroup`，这意味着：
- 可以像操作单个对象一样操作整个组件
- 可以使用 `.center()`, `.shift()`, `.scale()` 等方法
- 组件内的所有子元素会一起变换

### 2. 坐标系统
- Manim 使用的是 3D 坐标系（但通常只在 xy 平面工作）
- 原点 (0,0,0) 在屏幕中心
- x 轴向右，y 轴向上

### 3. 旋转与定位
```python
# 旋转对象
block.rotate(angle_rad, about_point=ORIGIN)

# 移动到指定位置
block.move_to(position)

# 相对移动
block.shift(direction * distance)
```

### 4. 箭头创建
```python
Arrow(
    start_point,      # 起点
    end_point,        # 终点
    buff=0,           # 箭头与端点的距离
    color=YELLOW,     # 颜色
    stroke_width=4    # 线宽
)
```

## 🛠️ 自定义扩展

### 添加新的力向量

编辑 `components/physics/mechanics.py`：

```python
# 在 __init__ 方法中添加
# 例如：添加外力 F_app
applied_force = self._create_force_vector(
    start_point=block_center,
    direction=rotate_vector(RIGHT, angle_rad),  # 沿斜面向上
    length=1.5,
    color=YELLOW,
    label=r"F_{app}"
)
self.applied_force = applied_force
```

### 修改颜色方案

```python
# 在 _create_force_vector 方法中修改
color={
    'gravity': RED,      # 重力颜色
    'normal': BLUE,      # 支持力颜色
    'friction': GREEN    # 摩擦力颜色
}[force_type]
```

## 📧 常见问题

### Q: 如何调整箭头大小？
A: 修改 `_create_force_vector` 方法中的 `length` 参数

### Q: 如何改变滑块位置？
A: 修改 `_calculate_block_position` 方法中的计算逻辑

### Q: 如何添加动画效果？
A: 使用 `self.play()` 方法，例如：
```python
self.play(Create(plane))           # 创建动画
self.play(plane.animate.shift(UP)) # 移动动画
self.play(FadeOut(plane))          # 淡出动画
```

## 🎯 下一步

1. 尝试修改参数，观察变化
2. 创建自己的测试场景
3. 添加更多物理组件（如弹簧、滑轮等）
4. 扩展组件功能，支持更复杂的物理场景

---

**祝你学习愉快！** 🎉
