# Manim 核心代码提取总结

## 提取概况

- **提取日期**: 2026-03-18
- **提取文件数**: 6 个核心文件
- **提取类总数**: 65 个类
- **输出位置**: `/Users/chenshutong/Desktop/3b1b/extracted_core/`

## 高价值目标目录

### 1. manimlib/mobject/ (40 个类)

#### geometry.py (28 个类)
- **Arc** - 基础圆弧类
- **Circle** - 圆形
- **Ellipse** - 椭圆
- **Annulus** - 环形
- **AnnularSector** - 环形扇形
- **Sector** - 扇形
- **ArcBetweenPoints** - 两点间的圆弧
- **CurvedArrow** - 曲线箭头
- **CurvedDoubleArrow** - 双向曲线箭头
- **TangentLine** - 切线
- **Line** - 直线
- **DashedLine** - 虚线
- **Elbow** - 角线（肘形线）
- **Arrow** - 箭头
- **Vector** - 向量
- **DoubleArrow** - 双向箭头
- **RightAngle** - 直角标记
- **Rectangle** - 矩形
- **Square** - 正方形
- **RoundedRectangle** - 圆角矩形
- **Polygon** - 多边形
- **RegularPolygon** - 正多边形
- **Triangle** - 三角形
- **ArrowTip** - 箭头尖端
- **ArrowCircleFilledTip** - 圆形填充箭头尖端
- **ArrowCircleTip** - 圆形箭头尖端
- **ArrowSquareTip** - 方形箭头尖端
- **ArrowSquareFilledTip** - 方形填充箭头尖端

#### vector_field.py (4 个类)
- **Vector** - 向量对象
- **VectorField** - 向量场（核心数学对象）
- **TimeVaryingVectorField** - 时变向量场
- **AnimatedStreamLines** - 动画流线

#### functions.py (3 个类)
- **FunctionGraph** - 函数图像
- **ParametricCurve** - 参数曲线
- **ParametricSurface** - 参数曲面

#### coordinate_systems.py (5 个类)
- **CoordinateSystem** - 坐标系统基类
- **Axes** - 坐标轴
- **ThreeDAxes** - 三维坐标轴
- **NumberPlane** - 数字平面（带网格）
- **ComplexPlane** - 复平面

### 2. manimlib/animation/ (25 个类)

#### creation.py (8 个类)
- **ShowPassingFlash** - 显示闪过效果
- **ShowCreation** - 显示创建动画
- **Uncreate** - 撤销创建动画
- **DrawBorderThenFill** - 先绘制边框后填充
- **Write** - 书写动画
- **Unwrite** - 撤销书写动画
- **AddTextLetterByLetter** - 逐字母添加文本
- **AddTextWordByWord** - 逐单词添加文本

#### transform.py (17 个类)
- **Transform** - 基础变换动画
- **ReplacementTransform** - 替换变换
- **TransformFromCopy** - 从副本变换
- **ApplyFunction** - 应用函数变换
- **ApplyPointwiseFunction** - 应用逐点函数
- **ApplyComplexFunction** - 应用复数函数
- **ApplyMatrix** - 应用矩阵变换
- **ApplyMethod** - 应用方法变换
- **FadeToColor** - 淡入颜色
- **FadeTransform** - 淡入变换
- **FadeTransformPieces** - 淡入变换各部分
- **MoveIntoView** - 移入视图
- **MovePoint** - 移动点
- **CyclicReplace** - 循环替换
- **Swap** - 交换
- **TransformShapes** - 变换形状
- **CountInFrom** - 从某数字计数显示

## 提取的内容类型

每个类生成两个文件：
1. **`.md` 文件** - 包含完整的文档信息
   - 类名和源位置
   - 文档字符串
   - 继承关系
   - 所有方法签名和文档

2. **`.py` 文件** - 包含代码框架
   - 类定义
   - 方法定义（带 pass 占位）
   - 类型注解
   - 参数信息

## 核心数学对象特征

### 几何图形
- 统一的参数化接口（arc_center, stroke_width, fill_color）
- 基于贝塞尔曲线的平滑绘制
- 支持点、线、面等基础几何构造

### 向量场
- 函数式定义：`func(x, y, z) -> vector`
- 可配置密度和采样策略
- 支持时间动态变化
- 颜色映射和幅度控制

### 坐标系统
- 统一的坐标变换接口
- 网格和轴线的自动生成
- 支持非线性变换
- 向量、点的空间表示

### 动画插值
- 纯数学插值函数（独立于场景）
- 支持 path_arc、path_func 等路径参数
- 可配置的时间控制（run_time, rate_func）
- 支持子对象的递归变换

## 避开的目录（已排除）

以下目录与渲染引擎和交互逻辑深度绑定，未提取：
- `camera/` - 相机系统
- `scene/` - 场景管理
- `window/` - 窗口交互
- `event_handler/` - 事件处理

## 下一步建议

1. **深入研究** - 重点关注 VectorField、CoordinateSystem 和 ParametricCurve
2. **数学核心** - 提取纯数学插值函数（如 smooth, there_and_back 等）
3. **类型系统** - 理解 Vect3、Point3D 等基础类型
4. **测试框架** - 验证提取的代码片段是否可独立运行
