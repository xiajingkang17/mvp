# 电磁学组件库使用说明

**文件位置**: `components/physics/electromagnetism.py`

**总组件数**: 10个

**开发日期**: 2026-02-08

---

## 📦 组件清单

| 序号 | 组件名 | 中文名 | 符号特征 |
|------|--------|--------|----------|
| 1 | `Battery` | 直流电源 | 长线(正极) + 短线(负极) + 黑色遮罩 |
| 2 | `Switch` | 单刀单掷开关 | 接线柱 + 刀闸 + 黑色遮罩 + 动画支持 |
| 3 | `Ammeter` | 电流表 | 圆圈(黑底白边) + 字母"A" + z_index修复 |
| 4 | `Voltmeter` | 电压表 | 圆圈(黑底白边) + 字母"V" + z_index修复 |
| 5 | `LightBulb` | 小灯泡 | 圆圈(黑底白边) + X形交叉线 |
| 6 | `Capacitor` | 电容器 | 两条平行竖线(等高) + 黑色遮罩 |
| 7 | `Rheostat` | 滑动变阻器 | 电阻主体 + 3个接线柱 + 滑片 + 箭头修复 |
| 8 | `Potentiometer` | 电位器 | 电阻主体 + 斜向穿透箭头 |
| 9 | `Inductor` | 电感器 | 连续拱门线圈(McDonald's style) + 黑色遮罩 |
| 10 | `LED` | 发光二极管 | 正三角形 + 垂直截止线 + 平行发射箭头 |

---

## 🎨 设计标准

### 全局规范

```python
from manim import *
from typing import Optional, Union
import numpy as np

# 所有组件继承自 VGroup
class ComponentName(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 默认生成在 ORIGIN 中心
```

### 视觉核心

| 特性 | 标准值 | 说明 |
|------|--------|------|
| 线条颜色 | `stroke_color=WHITE` | 白色线条 |
| 线条宽度 | `stroke_width=4.0` | 4像素宽 |
| 填充颜色 | `fill_color=BLACK` | 黑色填充 |
| 填充不透明度 | `fill_opacity=1.0` | 完全不透明（遮挡背景） |
| z-index控制 | `set_z_index()` | 使用方法，不直接赋值 |

### 遮挡逻辑（关键）

所有封闭图形组件必须有**黑色背景遮罩**：

```python
# 最底层：黑色遮罩（遮挡网格线）
background_mask = Rectangle(
    fill_color=BLACK,
    fill_opacity=1.0,
    stroke_opacity=0  # 无边框
)
background_mask.z_index = -10

# 上层：白色线条
component.z_index = 0
```

### 接口方法

所有组件必须实现：

```python
def get_left_terminal(self) -> np.ndarray:
    """返回左侧接线端点坐标 [x, y, z]"""
    return self.left_wire.get_start()

def get_right_terminal(self) -> np.ndarray:
    """返回右侧接线端点坐标 [x, y, z]"""
    return self.right_wire.get_end()
```

---

## 🔧 特殊修正记录

### 1. Ammeter & Voltmeter（电表）

**问题**: 字母闪烁或不可见

**修复**: 显式设置 z-index

```python
label.set_z_index(2)  # 确保字母在圆圈之上
```

### 2. Rheostat（滑动变阻器）

**问题**: 滑片箭头穿过电阻主体

**修复**: 调整箭头尖端坐标

```python
arrow = Polygon(
    [x - size, top + height, 0],  # 左上角
    [x + size, top + height, 0],  # 右上角
    [x, top, 0],                  # 尖端（刚好在上边缘）
)
```

### 3. Inductor（电感器）

**问题**: 波浪线（上下交替）

**修复**: 改为连续拱门

```python
# ❌ 错误：交替方向
if i % 2 == 0:
    arc = Arc(..., angle=-PI)  # 向上
else:
    arc = Arc(..., angle=PI)   # 向下

# ✅ 正确：统一向上
arc = Arc(radius, start_angle=PI, angle=-PI)  # 全部向上
arc.shift(RIGHT * (i * 2 * radius))
```

### 4. LED（发光二极管）

**问题1**: 三角形不是正三角形

**修复**: 使用正三角形公式

```python
height = side_length * np.sqrt(3) / 2
```

**问题2**: 箭头不平行

**修复**: 使用复制+平移方法

```python
arrow1 = Arrow(...).rotate(135 * DEGREES)
arrow2 = arrow1.copy()  # 复制！
arrow2.shift(RIGHT * 0.25 + UP * 0.15)  # 平移！
```

---

## 📖 快速开始

### 基础使用

```python
from manim import *
from components.physics.electromagnetism import *

class TestScene(Scene):
    def construct(self):
        # 创建组件
        battery = Battery(
            height=0.8,
            ratio=0.55,
            wire_length=0.5
        )

        resistor = Resistor(
            width=2.0,
            height=0.5,
            lead_length=0.8
        )

        # 添加到场景
        self.add(battery)
        self.add(resistor.shift(RIGHT * 3))
```

### 电路连接示例

```python
def create_circuit(self):
    # 创建元件
    battery = Battery()
    switch = Switch(is_closed=False)
    ammeter = Ammeter()

    # 获取接线端点
    pos_terminal = battery.get_positive_terminal()
    neg_terminal = battery.get_negative_terminal()

    # 连接线路
    wire1 = Line(pos_terminal, switch.get_left_terminal())
    wire2 = Line(switch.get_right_terminal(), ammeter.get_left_terminal())

    # 组合电路
    circuit = VGroup(battery, switch, ammeter, wire1, wire2)
    return circuit
```

### 动画示例

```python
class SwitchAnimation(Scene):
    def construct(self):
        switch = Switch(is_closed=False)

        # 闭合开关
        self.play(switch.close(), run_time=1.0)
        self.wait(1)

        # 断开开关
        self.play(switch.open(), run_time=1.0)
```

---

## 🎯 参数速查表

| 组件 | 主要参数 | 默认值 | 说明 |
|------|----------|--------|------|
| `Battery` | `height`, `ratio`, `plate_spacing` | 0.8, 0.55, 0.3 | 正极高度、负极比例、极板间距 |
| `Switch` | `switch_length`, `is_closed`, `open_angle` | 0.8, False, 30° | 开关长度、状态、张角 |
| `Ammeter` | `radius`, `label_scale` | 0.4, 0.7 | 圆半径、字母缩放 |
| `Voltmeter` | `radius`, `label_scale` | 0.4, 0.7 | 圆半径、字母缩放 |
| `LightBulb` | `radius` | 0.5 | 圆半径 |
| `Capacitor` | `height`, `plate_spacing` | 0.8, 0.3 | 极板高度、间距 |
| `Rheostat` | `body_width`, `alpha` | 2.0, 0.5 | 主体宽度、滑片位置 |
| `Potentiometer` | `body_width`, `arrow_scale` | 1.2, 1.5 | 主体宽度、箭头长度倍数 |
| `Inductor` | `num_loops`, `radius` | 4, 0.2 | 线圈圈数、半圆半径 |
| `LED` | `side_length`, `arrow_size` | 1.2, 0.6 | 正三角形边长、箭头长度 |

---

## 📚 完整API文档

详细的API文档请查看各组件的docstring，每个组件都包含：

- 功能描述
- 参数说明
- 使用示例
- 接口方法说明

```python
help(Battery)  # 查看Battery组件的完整文档
```

---

## ⚠️ 注意事项

1. **z-index 问题**: 始终使用 `set_z_index()` 方法，不要直接赋值 `z_index` 属性
2. **遮挡逻辑**: 封闭图形组件必须有黑色背景遮罩
3. **居中定位**: 所有组件默认生成在 `ORIGIN`，使用 `shift()` 调整位置
4. **类型注解**: 接口方法返回 `np.ndarray` 类型
5. **动画兼容**: `Switch` 组件的动画方法返回 `Rotate` 对象

---

## 🚀 未来扩展

可以考虑添加的组件：

- [ ] 电动机 (Motor) - 圆圈 + 字母 "M"
- [ ] 发电机 (Generator) - 圆圈 + 字母 "G"
- [ ] 变压器 (Transformer) - 两个线圈 + 铁芯
- [ ] 继电器 (Relay) - 线圈 + 触点
- [ ] 晶体管 (Transistor) - 三极管符号
- [ ] 运算放大器 (OpAmp) - 三角形 + 输入输出端

---

**维护者**: Manim 物理组件库开发团队

**最后更新**: 2026-02-08
