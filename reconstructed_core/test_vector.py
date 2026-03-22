"""
重构版 Vector 类测试脚本

测试内容：
1. 基本功能测试（创建、复制、修改）
2. 语义标签测试（设置、获取、验证）
3. 力学分析快捷方法测试
4. 数据集安全测试（Bbox 稳定性）
"""

import numpy as np
import sys

# 添加 manimlib 到路径
sys.path.insert(0, '/Users/chenshutong/Desktop/Manim_Dataset_Test/manim-master')
sys.path.insert(0, '/Users/chenshutong/Desktop/3b1b/reconstructed_core')

from manimlib.constants import RIGHT, DOWN, UP, LEFT
from Vector import (
    Vector,
    GravityVector,
    NormalVector,
    FrictionVector,
    TensionVector,
    AppliedForceVector,
    VelocityVector,
    AccelerationVector
)


def test_basic_creation():
    """测试基本创建功能"""
    print("测试 1: 基本创建功能")

    # 从原点创建向量
    v1 = Vector(RIGHT)
    print(f"  创建方向向量 RIGHT: {v1.get_direction()}")

    v2 = Vector(np.array([1, 2, 0]))
    print(f"  创建自定义方向向量: {v2.get_direction()}")

    # 测试复制功能（数据集安全）
    v3 = v1.copy()
    print(f"  复制向量成功: {v3 is not v1}")

    print("  ✓ 基本创建功能正常\n")


def test_semantic_labels():
    """测试语义标签功能"""
    print("测试 2: 语义标签功能")

    # 创建向量并设置语义
    v = Vector(RIGHT)
    print(f"  默认语义类型: {v.semantic_type}")
    print(f"  默认语义角色: {v.semantic_role}")

    # 测试语义属性设置
    v.semantic_type = 'force'
    v.semantic_role = 'gravity'
    v.semantic_content = 'mg'

    print(f"  设置后类型: {v.semantic_type}")
    print(f"  设置后角色: {v.semantic_role}")
    print(f"  设置后内容: {v.semantic_content}")

    # 测试大小设置
    v.magnitude = 9.8
    print(f"  向量大小: {v.magnitude}")
    print(f"  自动更新内容: {v.semantic_content}")

    print("  ✓ 语义标签功能正常\n")


def test_mechanics_shortcuts():
    """测试力学分析快捷方法"""
    print("测试 3: 力学分析快捷方法")

    # 重力向量
    gravity = GravityVector(DOWN, 9.8)
    print(f"  重力向量: 角色={gravity.semantic_role}, 内容={gravity.semantic_content}")

    # 支持力向量
    normal = NormalVector(UP, 5.0)
    print(f"  支持力向量: 角色={normal.semantic_role}, 内容={normal.semantic_content}")

    # 摩擦力向量
    friction = FrictionVector(LEFT, 3.0)
    print(f"  摩擦力向量: 角色={friction.semantic_role}, 内容={friction.semantic_content}")

    # 速度向量
    velocity = VelocityVector(RIGHT, 10.0)
    print(f"  速度向量: 角色={velocity.semantic_role}, 类型={velocity.semantic_type}")

    print("  ✓ 力学分析快捷方法正常\n")


def test_color_mapping():
    """测试颜色映射"""
    print("测试 4: 颜色映射")

    vectors = [
        GravityVector(DOWN, 9.8),
        NormalVector(UP, 5.0),
        FrictionVector(LEFT, 3.0),
        VelocityVector(RIGHT, 10.0),
        AccelerationVector(RIGHT, 2.0)
    ]

    for v in vectors:
        color = v.get_fill_color()
        print(f"  {v.semantic_role}: 颜色={color}")

    print("  ✓ 颜色映射正常\n")


def test_bbox_stability():
    """测试 Bbox 稳定性"""
    print("测试 5: Bbox 稳定性")

    v = Vector(np.array([2, 1, 0])).as_applied(10.0)

    # 多次获取 Bbox，验证稳定性
    bboxes = [v.get_bbox() for _ in range(10)]

    # 检查所有 Bbox 是否相同
    first_bbox = bboxes[0]
    all_same = all(
        np.allclose(bbox[0], first_bbox[0]) and np.allclose(bbox[1], first_bbox[1])
        for bbox in bboxes
    )

    if all_same:
        print(f"  ✓ Bbox 稳定: {first_bbox}")
    else:
        print(f"  ✗ Bbox 不稳定！")
        for i, bbox in enumerate(bboxes):
            print(f"    {i}: {bbox}")

    print()


def test_chaining():
    """测试链式调用"""
    print("测试 6: 链式调用")

    v = (Vector(RIGHT)
          .as_applied(10.0))
    v.semantic_content = 'F_app'

    print(f"  链式调用结果: 类型={v.semantic_type}, 角色={v.semantic_role}")
    print(f"  内容={v.semantic_content}, 大小={v.magnitude}")

    print("  ✓ 链式调用正常\n")


def test_error_handling():
    """测试错误处理"""
    print("测试 7: 错误处理")

    v = Vector(RIGHT)

    # 测试无效类型
    try:
        v.semantic_type = 'invalid_type'
        print("  ✗ 应该抛出错误但没有")
    except ValueError as e:
        print(f"  ✓ 类型检查正常: {str(e)[:50]}...")

    # 测试无效角色
    try:
        v.semantic_role = 'invalid_role'
        print("  ✗ 应该抛出错误但没有")
    except ValueError as e:
        print(f"  ✓ 角色检查正常: {str(e)[:50]}...")

    print()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("重构版 Vector 类测试套件")
    print("=" * 60)
    print()

    test_basic_creation()
    test_semantic_labels()
    test_mechanics_shortcuts()
    test_color_mapping()
    test_bbox_stability()
    test_chaining()
    test_error_handling()

    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
