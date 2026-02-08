# InclinedPlane 组件修复说明

## 📝 修复日期
2026-02-06

## 🎯 修复目标
修复 `InclinedPlane` (斜面) 组件的几何逻辑和角度标注，使其符合物理图示标准。

## ❌ 修复前的问题

### 几何结构问题
- **顶点位置混乱**：以中心为基准，左右对称
- **直角位置错误**：不是标准的左下角直角
- **角度标注位置错误**：标注在左侧，而非右下角

### 视觉效果
- 形状不符合标准物理图示
- 角度标注位置不合理
- 难以理解和教学使用

## ✅ 修复后的效果

### 几何结构（标准定义）

#### 顶点位置
```
左上角 (Top-Left)
    •
    |\
    |  \
    |    \  斜边
高度 |     \
    |      \
    |       \
    •________•
左下角    右下角
(直角)   (斜面底角 θ)
  底边长度 L
```

#### 坐标定义
- **左下角** (Bottom-Left): `ORIGIN` (0, 0, 0) - **直角 (90°)**
- **右下角** (Bottom-Right): `RIGHT * length` (L, 0, 0) - **斜面底角 θ**
- **左上角** (Top-Left): `UP * height` (0, h, 0) - **顶点**

#### 参数计算
```python
height = length × tan(θ)
```

## 📊 修复对比

| 特性 | 修复前 | 修复后 |
|------|--------|--------|
| **几何结构** | ❌ 中心对称分布 | ✅ 标准直角三角形 |
| **直角位置** | ❌ 不固定 | ✅ 左下角 (0, 0) |
| **角度标注位置** | ❌ 左侧 | ✅ 右下角 ✓ |
| **顶点位置** | ❌ 顶部居中 | ✅ 左上角 |
| **底边位置** | ❌ 居中 | ✅ 从原点向右 |
| **符合物理图示** | ❌ 否 | ✅ 是 |

## 🎨 视觉效果说明

### 标准物理图示
- **直角**：在左下角，清晰标注
- **斜面底角 θ**：在右下角，带弧线标注
- **顶点**：在左上角，最高点
- **底边**：水平，从左到右
- **斜边**：从右下角向左上角倾斜

### 角度标注
- **位置**：右下角 (Bottom-Right)
- **弧线**：从底边逆时针到斜边
- **标签**：希腊字母 θ
- **颜色**：与斜面同色

## 🔧 代码实现

### 关键代码（修复后）

```python
class InclinedPlane(VGroup):
    """
    斜面组件

    直角三角形，左下角为直角，右下角标注角度 θ
    """

    def __init__(
        self,
        angle: float = 30,
        length: float = 5.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        fill_color: str = BLUE_E,
        fill_opacity: float = 0.3,
        show_angle: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES
        height = length * math.tan(angle_rad)

        # 定义三个顶点
        p_bottom_left = ORIGIN           # 左下角：直角 (90°)
        p_bottom_right = RIGHT * length   # 右下角：斜面底角 θ
        p_top_left = UP * height         # 左上角：顶点

        # 绘制直角三角形
        triangle = Polygon(
            p_bottom_left,
            p_bottom_right,
            p_top_left,
            color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity
        )

        self.add(triangle)

        # 角度标注（在右下角）
        if show_angle:
            # 角度弧线
            arc_radius = 0.6
            angle_arc = Arc(
                radius=arc_radius,
                start_angle=PI,      # 从左边开始（180度）
                angle=-angle_rad,    # 顺时针旋转 -angle 度
                color=color,
                stroke_width=stroke_width * 0.8
            )
            angle_arc.shift(p_bottom_right)

            # 角度标签 θ
            angle_label = MathTex(r"\theta", font_size=36, color=color)
            label_offset = np.array([
                -arc_radius * 1.2,
                arc_radius * 0.3,
                0
            ])
            angle_label.move_to(p_bottom_right + label_offset)

            self.add(angle_arc, angle_label)
```

## 📐 几何计算

### 高度计算
```python
height = length × tan(θ)
```

**示例：**
- θ = 30°, length = 5.0 → height ≈ 2.89
- θ = 45°, length = 5.0 → height = 5.0
- θ = 60°, length = 5.0 → height ≈ 8.66

### 角度弧线绘制
```python
Arc(
    radius=0.6,
    start_angle=PI,        # 从左侧（180度）开始
    angle=-angle_rad,     # 顺时针旋转 -angle 度
)
```

## 🎬 测试场景

### 可用测试
1. **TestInclinedPlaneFixed** - 标准展示
2. **TestInclinedPlaneComparison** - 不同角度对比
3. **TestInclinedPlaneDetail** - 几何结构细节
4. **TestInclinedPlaneGeometry** - 几何解释

### 运行命令
```bash
# 标准展示
python3.11 -m manim -pql cases/physics_test/test_inclined_plane_fix.py TestInclinedPlaneFixed

# 对比展示
python3.11 -m manim -pql cases/physics_test/test_inclined_plane_fix.py TestInclinedPlaneComparison

# 细节展示
python3.11 -m manim -pql cases/physics_test/test_inclined_plane_fix.py TestInclinedPlaneDetail

# 几何解释
python3.11 -m manim -pql cases/physics_test/test_inclined_plane_fix.py TestInclinedPlaneGeometry
```

### 视频位置
```
/Users/chenshutong/Desktop/mvp/mvp/mvp-main/media/videos/test_inclined_plane_fix/480p15/
```

## ✨ 修复亮点

1. ✅ **标准化** - 完全符合物理图示规范
2. ✅ **几何清晰** - 顶点位置明确
3. ✅ **角度正确** - θ 标注在正确位置
4. ✅ **代码简洁** - 使用标准坐标定义
5. ✅ **易于理解** - 符合直觉和教学需求

## 📐 坐标系统说明

### 标准坐标
```
y (UP)
  ↑
  |
  |    • Top-Left (0, h)
  |    |\
  |    |  \
  |    |    \
  |____|_____\_____________→ x (RIGHT)
  ORIGIN      • Bottom-Right (L, 0)
  (0,0)
```

### 顶点命名
- **Bottom-Left**: 左下角，原点，直角位置
- **Bottom-Right**: 右下角，底边终点，角度标注位置
- **Top-Left**: 左上角，顶点，最高点

## 💡 使用示例

### 基本使用
```python
from components.physics.mechanics_full import InclinedPlane

class Example(Scene):
    def construct(self):
        # 创建30度斜面
        plane = InclinedPlane(angle=30, length=5.0)
        self.add(plane)
```

### 自定义样式
```python
# 45度斜面，更小的尺寸
plane = InclinedPlane(
    angle=45,
    length=4.0,
    color=YELLOW,
    stroke_width=6.0
)
```

### 不显示角度标注
```python
plane = InclinedPlane(
    angle=30,
    length=5.0,
    show_angle=False  # 不显示角度
)
```

## 📐 几何关系

### 三角函数关系
```
        /|
       / |
      /  |
     /   |
    /    | h (height)
   /     |
  /______|
 L (length)

tan(θ) = h / L
h = L × tan(θ)
```

### 常用角度
| 角度 θ | tan(θ) | height (L=5) |
|--------|--------|---------------|
| 15° | 0.268 | 1.34 |
| 30° | 0.577 | 2.89 |
| 45° | 1.000 | 5.00 |
| 60° | 1.732 | 8.66 |

## 🎯 应用场景

### 物理教学
- �面运动分析
- 摩擦力演示
- 力的分解

### 习题讲解
- 滑块沿斜面下滑
- 斜面上的力学问题
- 功和能量计算

### 实验模拟
- 理想斜面实验
- 伽利略斜面实验
- 摩擦实验

---

**修复完成！** ✅
InclinedPlane 组件现在完全符合物理图示标准。
