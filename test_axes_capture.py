import sys
import os
from pathlib import Path

# 当前 3b1b 目录
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "washed_manim_components"))

# ==========================================
# 【绝对暴力定位】直接硬编码旧目录的绝对路径！
# ==========================================
OLD_TEST_DIR = "/Users/chenshutong/Desktop/Manim_Dataset_Test"
sys.path.append(OLD_TEST_DIR)

from manimlib import *
from data_gen_base import DataGenScene

# 动态引入洗净的 Axes
try:
    from Washed_Axes import Axes
except ImportError:
    print("⚠ 尚未找到 Washed_Axes.py，请等待大模型清洗完成！")
    sys.exit(1)

class TestAxesCapture(DataGenScene):
    def construct(self):
        # 1. 实例化洗净的坐标轴
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-4, 4, 1],
            axis_config={"color": BLUE}
        )

        # 2. 播放入场动画
        self.play(ShowCreation(axes))
        self.wait(1)
        
        # 3. 简单的变换测试
        axes_target = axes.copy().shift(RIGHT * 2).scale(0.8)
        self.play(Transform(axes, axes_target))
        self.wait(1)

# 这一行必须完全顶格！（左边不能有任何空格）
if __name__ == "__main__":
    # 配置输出数据集的路径
    dataset_output_dir = Path("/Users/chenshutong/Desktop/Manim_Dataset_Output/datasets")
    dataset_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 模拟命令行参数传给 ManimGL
    sys.argv = ["manimgl", __file__, "TestAxesCapture", "-l", "-w"]
    
    # 【核心修复】：显式导入 __main__ 模块并调用
    import manimlib.__main__
    manimlib.__main__.main()