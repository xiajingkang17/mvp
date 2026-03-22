"""
向量组件数据集抓取集成测试

验证重构的物理向量类能否被照相机基类正确抓取
"""

from manimlib import *
from manimlib.scene.scene import Scene
from manimlib.constants import *
from manimlib.mobject.geometry import Square

# 导入重构的向量类
import sys
sys.path.insert(0, '/Users/chenshutong/Desktop/3b1b/reconstructed_core')
from Vector import GravityVector, NormalVector

# 导入数据集生成基类
# 注意：如果实际基类名不是 DataGenScene，请修改此导入
try:
    from data_gen_base import DataGenScene
except ImportError:
    # 临时回退到普通 Scene，实际使用时请确保 data_gen_base.py 存在
    print("警告: 未找到 data_gen_base.py，使用普通 Scene 进行测试")
    print("请在项目目录下创建 data_gen_base.py 并定义 DataGenScene 基类")
    DataGenScene = Scene


class TestVectorScene(DataGenScene):
    """
    向量组件抓取测试场景

    测试内容：
    1. 创建木块（正方形）
    2. 生成重力向量和支持力向量
    3. 验证初始状态的 Bbox 抓取
    4. 验证位移后的 Bbox 抓取和状态计算
    """

    def construct(self):
        # 1. 创建木块（正方形）
        square = Square(side_length=2.0, color=BLUE, fill_opacity=0.3)
        square.move_to(ORIGIN)

        # 2. 从木块中心生成重力向量（向下）
        gravity = GravityVector(DOWN * 2.5, 9.8)
        gravity.move_to(square.get_center())

        # 3. 从木块中心生成支持力向量（向上）
        normal = NormalVector(UP * 2.5, 9.8)
        normal.move_to(square.get_center())

        # 4. 播放动画 - 触发底层基类的抓取逻辑
        # 这里会抓取所有对象的初始 Bbox 状态（status: new）
        self.play(
            FadeIn(square),
            GrowArrow(gravity),
            GrowArrow(normal)
        )

        # 添加标签（用于视觉验证）
        gravity_label = Tex("mg", color=YELLOW).next_to(gravity, RIGHT)
        normal_label = Tex("N", color=BLUE).next_to(normal, RIGHT)

        self.play(
            Write(gravity_label),
            Write(normal_label)
        )

        self.wait(0.5)

        # 5. 测试位移后的抓取
        # 所有对象向右移动，触发 Bbox 更新（status: keep）
        self.play(
            square.animate.shift(RIGHT * 2),
            gravity.animate.shift(RIGHT * 2),
            normal.animate.shift(RIGHT * 2),
            gravity_label.animate.shift(RIGHT * 2),
            normal_label.animate(shift(RIGHT * 2))
        )

        self.wait(0.5)

        # 6. 测试旋转后的抓取（验证复杂变换）
        self.play(
            Rotate(square, 30 * DEGREES),
            Rotate(gravity, 30 * DEGREES, about_point=square.get_center()),
            Rotate(normal, 30 * DEGREES, about_point=square.get_center())
        )

        self.wait(1)


# 运行测试
if __name__ == "__main__":
    TestVectorScene()
