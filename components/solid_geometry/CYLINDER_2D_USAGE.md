# 圆柱组件使用指南（2D 拼装法）

## 概述

`CylinderOblique` 采用**"2D 拼装法"**（Schematic Approach）绘制中国高中教材风格的斜二测圆柱。不使用复杂的 3D 投影计算，而是像在黑板上画图一样，直接用 2D 几何形状组装圆柱。

## 核心特性

✅ **2D 拼装法**: 直接用几何形状（Arc、Ellipse、Line）组装
✅ **参数简单**: 只有 `radius`、`height`、`skew_factor` 三个核心参数
✅ **直观可控**: 像在黑板上画图一样，所见即所得
✅ **分段坐标轴**: 内部虚线，外部实线
✅ **标准教材风格**: 完美复刻高中数学教材的斜二测画法

## 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `radius` | float | 1.5 | 圆柱半径（屏幕上的水平宽度的一半） |
| `height` | float | 3.0 | 圆柱高度（屏幕上的垂直高度） |
| `skew_factor` | float | 0.4 | 压缩比（把圆压扁成椭圆，0.4 表示高度是宽度的 40%） |
| `x_axis_angle` | float | -135° | X 轴倾斜角度（斜二测标准） |
| `show_axes` | bool | True | 是否显示坐标轴 |
| `show_labels` | bool | True | 是否显示标签 |
| `origin_offset` | np.ndarray | None | 原点偏移（默认居中） |

## 基本用法

### 最简单的示例

```python
from manim import *
from components.solid_geometry.cylinder import CylinderOblique

class MyCylinderScene(Scene):
    def construct(self):
        # 创建圆柱（使用默认参数）
        cylinder = CylinderOblique()

        # 添加到场景
        self.add(cylinder)
```

### 自定义参数

```python
class CustomCylinderScene(Scene):
    def construct(self):
        # 创建自定义圆柱
        cylinder = CylinderOblique(
            radius=2.0,              # 半径
            height=3.5,              # 高度
            skew_factor=0.4,         # 压缩比（0.4 = 40%）
            x_axis_angle=-135 * DEGREES,  # X 轴倾斜角度
            show_axes=True,          # 显示坐标轴
            show_labels=True         # 显示标签
        )

        self.add(cylinder)
```

## 绘制逻辑（2D 拼装法）

组件按以下顺序组装圆柱：

### 1. 内部坐标轴（虚线，底层）

```python
# Z 轴 Inner：O → O'（竖直向上）
DashedLine(center_bottom, center_top)

# Y 轴 Inner：O → 右侧棱底部（水平向右）
DashedLine(center_bottom, right_point_bottom)

# X 轴 Inner：O → 椭圆边界（斜向左下）
DashedLine(center_bottom, x_direction * radius * 0.9)
```

### 2. 底部椭圆（分段绘制）

```python
# 后半段（上半弧）：虚线
back_arc = Arc(
    radius=radius,
    start_angle=0°,      # RIGHT
    angle=180°,          # 到 LEFT
    arc_center=center_bottom
)
back_arc.stretch(skew_factor, dim=1)  # 压扁成椭圆
back_arc = DashedVMobject(back_arc)

# 前半段（下半弧）：实线
front_arc = Arc(
    radius=radius,
    start_angle=180°,    # LEFT
    angle=180°,          # 到 RIGHT
    arc_center=center_bottom
)
front_arc.stretch(skew_factor, dim=1)  # 压扁成椭圆
```

### 3. 侧面轮廓（两条竖直线）

```python
# 左棱：连接底部左端点和顶部左端点
Line(left_point_bottom, left_point_top)

# 右棱：连接底部右端点和顶部右端点
Line(right_point_bottom, right_point_top)
```

### 4. 顶部椭圆（完整实线）

```python
Ellipse(
    width=2 * radius,
    height=2 * radius * skew_factor,
    arc_center=center_top
)
```

### 5. 外部坐标轴（实线箭头）

```python
# Z 轴 Outer：O' → 箭头终点
Arrow(center_top, center_top + UP * extension)

# Y 轴 Outer：右侧棱底部 → 箭头终点
Arrow(right_point_bottom, right_point_bottom + RIGHT * extension)

# X 轴 Outer：内部端点 → 箭头终点
Arrow(x_inner_end, x_inner_end + x_direction * extension)
```

### 6. 标签（O 和 O'）

```python
# 底面圆心 O（向下偏移）
label_o = MathTex("O")
label_o.move_to(center_bottom + DOWN * 0.5)

# 顶面圆心 O'（向上偏移）
label_o_prime = MathTex("O'")
label_o_prime.move_to(center_top + UP * 0.5)
```

## 参数调整指南

### 压缩比（skew_factor）

控制椭圆的"扁平程度"：

- `0.3`: 很扁（接近水平线）
- `0.4`: 标准（教材风格）
- `0.5`: 较圆（接近正圆）

```python
# 很扁的椭圆
cylinder = CylinderOblique(skew_factor=0.3)

# 标准椭圆
cylinder = CylinderOblique(skew_factor=0.4)

# 较圆的椭圆
cylinder = CylinderOblique(skew_factor=0.5)
```

### X 轴倾斜角度（x_axis_angle）

控制 X 轴的方向：

- `-135°`: 标准（斜二测，指向左下）
- `-120°`: 较平（指向偏左）
- `-150°`: 较陡（指向偏下）

```python
# 标准 X 轴
cylinder = CylinderOblique(x_axis_angle=-135 * DEGREES)

# 较平的 X 轴
cylinder = CylinderOblique(x_axis_angle=-120 * DEGREES)

# 较陡的 X 轴
cylinder = CylinderOblique(x_axis_angle=-150 * DEGREES)
```

## 访问几何数据

```python
cylinder = CylinderOblique()

# 获取圆心位置
bottom_center = cylinder.get_center_bottom()
top_center = cylinder.get_center_top()

# 获取侧棱端点
left_bottom, right_bottom = cylinder.get_side_edge_points_bottom()
left_top, right_top = cylinder.get_side_edge_points_top()

# 访问参数
print(f"半径: {cylinder.radius}")
print(f"高度: {cylinder.height}")
print(f"压缩比: {cylinder.skew_factor}")
```

## 完整示例

```python
from manim import *
from components.solid_geometry.cylinder import CylinderOblique

class CylinderExample(Scene):
    def construct(self):
        # 创建圆柱
        cylinder = CylinderOblique(
            radius=2.0,
            height=3.5,
            skew_factor=0.4
        )

        # 添加到场景
        self.add(cylinder)

        # 添加半径标注
        radius_line = DashedLine(
            start=cylinder.center_bottom,
            end=cylinder.right_point_bottom,
            color=GRAY,
            stroke_width=2
        )
        self.add(radius_line)

        # 添加标题
        title = Text("斜二测圆柱", font_size=36)
        title.to_edge(UP)
        self.add(title)
```

## 技术细节

### 2D 拼装法 vs 3D 投影法

| 特性 | 2D 拼装法 | 3D 投影法 |
|------|-----------|-----------|
| 复杂度 | 简单 | 复杂 |
| 可控性 | 高 | 中 |
| 计算量 | 小 | 大 |
| 直观性 | 高（像画图） | 中（需理解投影） |
| 精确度 | 中（视觉近似） | 高（数学精确） |

### 绘制顺序的重要性

组件严格按照以下顺序绘制，确保正确的遮挡关系：

1. **Inner Axes**（虚线，最底层）
2. **Bottom Ellipse**（分段椭圆）
3. **Side Edges**（侧棱）
4. **Top Ellipse**（顶部椭圆）
5. **Outer Axes**（实线箭头）
6. **Labels**（标签，最顶层）

### 椭圆的实现方式

底部椭圆使用两个 `Arc` 拼接：

```python
# 后半段（上半弧）：0° → 180°
back_arc = Arc(radius=radius, start_angle=0°, angle=180°)
back_arc.stretch(skew_factor, dim=1)  # 压扁

# 前半段（下半弧）：180° → 360°
front_arc = Arc(radius=radius, start_angle=180°, angle=180°)
front_arc.stretch(skew_factor, dim=1)  # 压扁
```

这种方式可以独立控制两段的颜色和虚实样式。

## 渲染命令

```bash
# 渲染圆柱组件演示
manim -pql tests/test_cube.py CylinderComponentDemo

# 渲染圆柱斜二测演示
manim -pql tests/test_cube.py CylinderObliqueDemo

# 高质量渲染
manim -pqh tests/test_cube.py CylinderComponentDemo
```

## 常见问题

**Q: 为什么使用 2D 拼装法而不是 3D 投影？**
A: 2D 拼装法更简单、更直观，参数易于调整，适合教学场景。

**Q: 如何调整椭圆的扁平程度？**
A: 调整 `skew_factor` 参数（0.3-0.5 之间）。

**Q: 如何改变 X 轴的方向？**
A: 调整 `x_axis_angle` 参数（推荐 -120° 到 -150°）。

**Q: 侧棱为什么是竖直的？**
A: 2D 拼装法直接使用竖直线连接左右端点，保证侧棱绝对竖直。

**Q: 如何调整圆柱的位置？**
A: 使用 `origin_offset` 参数或直接调用 `cylinder.shift()`。

## 更新日志

- **2026-02-18**: 完全重写组件
  - 采用 2D 拼装法
  - 简化参数（radius、height、skew_factor）
  - 移除复杂的 3D 投影计算
  - 优化代码结构和文档
