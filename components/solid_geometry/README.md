# 立体几何组件库 (Solid Geometry Components)

基于 Manim 的立体几何组件库，符合中国高中数学教材风格。

## 文件结构

```
components/solid_geometry/
├── __init__.py          # 模块初始化
├── solid_base.py        # 基类（虚实线处理）
├── cube.py              # 正方体组件（3D 透视投影）
├── oblique_cube.py      # 斜二测正方体组件（2D 平行投影）
└── README.md            # 本文档
```

## 核心特性

1. **两种投影模式**
   - **3D 透视投影**（`CubeGeometry`）：真实 3D 效果，支持相机旋转
   - **斜二测画法**（`ObliqueCube`）：教材标准，45° 平行投影

2. **教材标准风格**
   - 看不见的棱边自动渲染为虚线（半透明灰色）
   - 看得见的棱边渲染为实线
   - 标签智能布局，避免遮挡

3. **灵活的配置**
   - 支持选择任意顶点作为坐标原点（3D 模式）
   - 可选显示坐标轴和顶点标签
   - 可自定义边长、缩短系数、倾斜角度

## 快速开始

### 方式一：3D 透视投影（`CubeGeometry`）

```python
from manim import *
from components.solid_geometry import CubeGeometry

class MyScene(ThreeDScene):
    def construct(self):
        # 设置 3D 相机视角
        self.set_camera_orientation(
            phi=60 * DEGREES,
            theta=-45 * DEGREES
        )

        # 创建正方体
        cube = CubeGeometry(
            side_length=2.5,
            origin_point="A",  # 以 A 点为原点
            show_axes=True,
            show_labels=True
        )

        self.add(cube)
        cube.update_dashed_lines()
```

### 方式二：斜二测画法（`ObliqueCube`）✨ 推荐

```python
from manim import *
from components.solid_geometry import ObliqueCube

class MyScene(Scene):
    def construct(self):
        # 创建斜二测正方体（教材标准）
        oblique_cube = ObliqueCube(
            side_length=2.5,
            shortening_factor=0.5,  # 缩短系数
            angle=PI / 4,           # 45° 倾角
            show_axes=True,
            show_labels=True
        )

        self.add(oblique_cube)
```

## 组件对比

| 特性 | CubeGeometry (3D) | ObliqueCube (斜二测) |
|------|------------------|-------------------|
| 投影方式 | 透视投影 | 平行投影 |
| 场景类型 | ThreeDScene | Scene（2D） |
| 相机控制 | 可旋转 | 固定 |
| 适用场景 | 动画、演示 | 教材、试卷 |
| 渲染速度 | 较慢 | 快速 |
| 教材标准 | - | ✅ 完全符合 |

### 基础用法

```python
from manim import *
from components.solid_geometry import Cube

class MyScene(ThreeDScene):
    def construct(self):
        # 设置斜二测视角
        self.set_camera_orientation(
            phi=60 * DEGREES,
            theta=-45 * DEGREES
        )

        # 创建正方体
        cube = Cube(
            side_length=2.0,
            origin_point="D",
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cube)

        # 添加 updater（确保虚实线正确渲染）
        cube.add_updater(lambda m: m.update_dashed_lines())

        self.wait()
```

### 高级用法

```python
from components.solid_geometry import CubeGeometry

class AdvancedScene(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 使用 CubeGeometry 获取更多控制
        cube = CubeGeometry(
            side_length=3.0,
            origin_point="A",  # 以 A 点为原点
            show_axes=True,
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )

        self.add(cube)

        # 自定义 updater
        def update_cube(mob):
            phi = self.renderer.camera.phi.get_value()
            theta = self.renderer.camera.theta.get_value()
            r = 15
            camera_pos = np.array([
                r * np.sin(phi) * np.cos(theta),
                r * np.cos(phi),
                r * np.sin(phi) * np.sin(theta)
            ])
            mob.update_dashed_lines(camera_pos)

        cube.add_updater(update_cube)

        self.wait()
```

## 参数说明

### CubeGeometry / Cube

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `side_length` | float | 2.0 | 棱长 |
| `origin_point` | str | "D" | 坐标原点（A/B/C/D/A1/B1/C1/D1） |
| `show_axes` | bool | True | 是否显示坐标轴 |
| `show_labels` | bool | True | 是否显示顶点标签 |
| `edge_color` | str | WHITE | 棱边颜色 |
| `vertex_color` | str | YELLOW | 顶点颜色 |
| `stroke_width` | float | 4.0 | 线宽 |

## 运行测试

```bash
# 完整演示
manim -pql tests/test_cube.py CubeDemo

# 简化演示
manim -pql tests/test_cube.py CubeSimpleDemo

# 多示例演示
manim -pql tests/test_cube.py CubeMultipleExamples
```

## 技术说明

### 坐标系转换

- **内部**: Manim 标准坐标系（x 右, y 上, z 外）
- **显示**: 通过预旋转实现斜二测效果（x 右, z 上, y 内）

### 虚实线判断

根据面法线与视线向量的点积判断面可见性：
- 点积 < 0：面朝向相机（可见）
- 点积 ≥ 0：面背向相机（不可见）

棱边可见性：
- 连接的两个面都不可见 → 虚线
- 至少一个面可见 → 实线

## 开发规范

1. 所有组件继承自 `PolyhedronBase`
2. 避免在 `MathTex` 中使用 f-string
3. 优先使用 Manim 原生类
4. 教材风格：看不见的用虚线，看得见的用实线

## 许可

MIT License
