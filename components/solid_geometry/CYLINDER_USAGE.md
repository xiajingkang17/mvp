# 圆柱组件使用指南

## 概述

`CylinderOblique` 是一个符合中国高中数学教材标准的斜二测圆柱组件，使用纯 2D 投影算法实现。

## 核心特性（2026-02-18 修正版）

✅ **侧棱强制对齐 Y 轴**: 侧棱连接 Y 轴端点 `(0, ±r, 0)`，确保视觉正确
✅ **椭圆按 3D 坐标分虚实**: 后半段（x < 0）虚线，前半段（x > 0）实线
✅ **坐标轴严格分段**: 内部虚线 + 外部实线，Y 轴内部段现已修复
✅ **纯 2D 投影**: 不使用 ThreeDScene，完全可预测的输出
✅ **遮罩层系统**: 正确处理坐标轴遮挡关系

## 核心修正说明

### 修正 1: 侧棱对齐 Y 轴端点

**之前的问题**: 使用极值扫描法（Screen-X 最小/最大值）找切点，导致侧棱不在正确位置。

**修正方案**: 侧棱强制连接 Y 轴端点 `(0, ±r, 0)`：
```python
# 底面 Y 轴端点
p_bottom_left_y = project(0, -radius, 0)   # (0, -r, 0)
p_bottom_right_y = project(0, radius, 0)   # (0, +r, 0)

# 顶面 Y 轴端点（通过平移保证竖直）
p_top_left_y = p_bottom_left_y + height_vector
p_top_right_y = p_bottom_right_y + height_vector
```

### 修正 2: 坐标轴严格分段

**之前的问题**: Y 轴在圆柱内部完全消失（缺少内部虚线段）。

**修正方案**: 严格按三段式绘制：
- **Z 轴**: Inner `(0,0,0)→(0,0,h)` 虚线 + Outer `(0,0,h)→箭头` 实线
- **Y 轴**: Inner `(0,0,0)→(0,r,0)` 虚线 + Outer `(0,r,0)→箭头` 实线
- **X 轴**: Inner `(0,0,0)→(r,0,0)` 虚线 + Outer `(r,0,0)→箭头` 实线

### 修正 3: 椭圆按 3D 坐标分虚实段

**之前的问题**: 使用 Screen-Y 值判断前后半段，不准确。

**修正方案**: 按 3D 坐标的 x 值正负分段：
- **后半段（虚线）**: 圆上 `x < 0` 的部分
- **前半段（实线）**: 圆上 `x >= 0` 的部分

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
            radius=2.0,              # 底面半径
            height=3.5,              # 圆柱高度
            num_samples=100,         # 采样精度（越高越圆滑）
            shortening_factor=0.5,   # 斜二测缩短系数（标准 0.5）
            angle=PI / 4,           # 倾斜角度（标准 45°）
            show_axes=True,          # 显示坐标轴
            show_labels=True,        # 显示标签
            origin_offset=LEFT * 2 + DOWN * 1  # 原点偏移
        )

        self.add(cylinder)
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `radius` | float | 1.5 | 底面半径 |
| `height` | float | 3.0 | 圆柱高度 |
| `num_samples` | int | 50 | 圆周采样精度（推荐 50-100） |
| `shortening_factor` | float | 0.5 | 斜二测缩短系数（标准值） |
| `angle` | float | PI/4 | 倾斜角度（弧度） |
| `show_axes` | bool | True | 是否显示坐标轴 |
| `show_labels` | bool | True | 是否显示标签 |
| `origin_offset` | np.ndarray | None | 原点偏移（默认居中） |

## 绘制顺序

组件按照以下顺序绘制，确保正确的遮挡关系：

1. **Inner Axes** (内部坐标轴，虚线)
   - Z 轴：原点 → 顶面圆心
   - Y 轴：原点 → 底面 (0, r, 0)
   - X 轴：原点 → 底面 (r, 0, 0)

2. **Masks** (遮罩层，黑色填充)
   - 底面椭圆遮罩
   - 顶面椭圆遮罩

3. **Geometry** (几何体)
   - 底面圆弧（后半虚线，前半实线）
   - 顶面椭圆（全部实线）
   - 侧棱（绝对竖直）

4. **Outer Axes** (外部坐标轴，实线箭头)
   - Z 轴：顶面圆心 → 箭头终点
   - Y 轴：底面 (0, r, 0) → 箭头终点
   - X 轴：底面 (r, 0, 0) → 箭头终点

5. **Labels** (标签)
   - 底面圆心 O
   - 顶面圆心 O'

## 访问几何数据

```python
cylinder = CylinderOblique()

# 获取圆心位置
bottom_center = cylinder.get_center_bottom()
top_center = cylinder.get_center_top()

# 获取切点位置
left_bottom, right_bottom = cylinder.get_tangent_points_bottom()
left_top, right_top = cylinder.get_tangent_points_top()

# 访问原始数据
print(f"半径: {cylinder.radius}")
print(f"高度: {cylinder.height}")
print(f"采样点数: {cylinder.num_samples}")
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
            num_samples=100
        )

        # 添加到场景
        self.add(cylinder)

        # 添加半径标注
        radius_point = cylinder.bottom_points_2d[0]
        radius_line = DashedLine(
            start=cylinder.center_bottom,
            end=radius_point,
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

### 投影公式

```
screen_x = u_y - u_x * v * cos(α)
screen_y = u_z - u_x * v * sin(α)
```

其中：
- `(u_x, u_y, u_z)` 是用户坐标
- `v` 是缩短系数（标准 0.5）
- `α` 是倾斜角度（标准 45°）

### 侧棱定位算法（修正版）

1. **固定锚点**: 使用 Y 轴端点 `(0, ±r, 0)` 作为侧棱锚点
2. **垂直平移**: 顶面锚点 = 底面锚点 + 高度向量
3. **保证竖直**: 侧棱向量 = `[0, h, 0]`（纯 Y 方向）

```python
# 底面 Y 轴端点
p_bottom_left_y = project(0, -radius, 0)
p_bottom_right_y = project(0, radius, 0)

# 高度向量
height_vector = project(0, 0, h) - project(0, 0, 0)

# 顶面 Y 轴端点（通过平移得到）
p_top_left_y = p_bottom_left_y + height_vector
p_top_right_y = p_bottom_right_y + height_vector
```

### 椭圆虚实分段算法（修正版）

按 3D 坐标的 x 值正负分段：

```python
for i in range(num_samples):
    theta = 2 * PI * i / num_samples
    x_3d = radius * cos(theta)  # 3D 坐标的 x 值

    if x_3d < 0:
        # 后半段（虚线）
        back_points.append(projected_point)
    else:
        # 前半段（实线）
        front_points.append(projected_point)
```

### 坐标轴分段算法

严格按三段式绘制：

```python
# Z 轴
z_inner = DashedLine(origin, center_top)      # 内部虚线
z_outer = Arrow(center_top, arrow_end)        # 外部实线

# Y 轴
y_inner = DashedLine(origin, (0, r, 0))       # 内部虚线
y_outer = Arrow((0, r, 0), arrow_end)         # 外部实线

# X 轴
x_inner = DashedLine(origin, (r, 0, 0))       # 内部虚线
x_outer = Arrow((r, 0, 0), arrow_end)         # 外部实线
```

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

**Q: 侧棱为什么不是竖直的？**
A: 请确保使用 `CylinderOblique` 组件，它会自动应用垂直矫正算法。

**Q: 坐标轴为什么被圆柱遮挡？**
A: 组件使用分段绘制法和遮罩层，内部坐标轴会被自动遮挡。

**Q: 如何调整圆柱的位置？**
A: 使用 `origin_offset` 参数或直接调用 `cylinder.shift()`。

**Q: 采样精度应该设置为多少？**
A: 推荐 50-100。更高会更圆滑，但渲染时间会更长。

## 更新日志

- **2026-02-18**: 完全重写组件
  - 实现垂直矫正算法
  - 实现分段坐标轴系统
  - 优化代码结构和文档
