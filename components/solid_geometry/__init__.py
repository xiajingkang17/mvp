"""
立体几何组件库 - Solid Geometry Components Library

包含常用的立体几何图形组件，符合中国高中数学教材风格。

组件列表：
【多面体 - Polyhedra】
- CubeOblique: 斜二测正方体组件（2D 平行投影）
- CuboidOblique: 斜二测长方体组件（2D 平行投影）
- PyramidOblique: 斜二测正四棱锥组件（2D 平行投影）
- TetrahedronOblique: 斜二测正三棱锥组件（2D 平行投影）
- PrismOblique: 斜二测直三棱柱组件（2D 平行投影）

【旋转体 - Solids of Revolution】
- CylinderOblique: 斜二测圆柱组件（2D 平行投影）
- ConeOblique: 斜二测圆锥组件（2D 平行投影）
- FrustumOblique: 斜二测圆台组件（2D 平行投影）
- SphereOblique: 斜二测球体组件（2D 平行投影，美术增强版）

使用示例：
    # 斜二测正方体
    from components.solid_geometry import CubeOblique
    cube = CubeOblique(side_length=2.5)
    self.add(cube)

    # 斜二测圆柱
    from components.solid_geometry import CylinderOblique
    cylinder = CylinderOblique(radius=2.0, height=3.5)
    self.add(cylinder)

    # 斜二测球体（增强版）
    from components.solid_geometry import SphereOblique
    sphere = SphereOblique(radius=2.0, show_meridian=True, show_intersection_dots=True)
    self.add(sphere)

作者: Manim 数学组件库
日期: 2026-02-19
版本: v2.0
"""

# 多面体
from .oblique_cube import ObliqueCube as CubeOblique
from .cuboid import CuboidOblique
from .pyramid import PyramidOblique, TetrahedronOblique
from .prism import PrismOblique, TriangularPrismOblique

# 旋转体
from .cylinder import CylinderOblique
from .cone import ConeOblique
from .frustum import FrustumOblique
from .sphere import SphereOblique

__all__ = [
    # 多面体
    'CubeOblique',
    'CuboidOblique',
    'PyramidOblique',
    'TetrahedronOblique',
    'PrismOblique',
    'TriangularPrismOblique',
    # 旋转体
    'CylinderOblique',
    'ConeOblique',
    'FrustumOblique',
    'SphereOblique',
]
