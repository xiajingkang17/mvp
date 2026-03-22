"""
Manim 核心类批量洗稿脚本

自动化清洗 3b1b 原始代码，注入语义标签，符合多模态数据集生成规范
移植自 code_gen.py 的 Tabcode 专属 API 逻辑
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 从环境变量读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")

# 验证配置
if not API_KEY:
    raise ValueError("未找到 OPENAI_API_KEY 环境变量，请检查 .env 文件")
if not BASE_URL:
    raise ValueError("未找到 OPENAI_BASE_URL 环境变量，请检查 .env 文件")

# 初始化 OpenAI 客户端（移植自 code_gen.py）
client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=180.0)


# ============================================================================
# 【不可违背的 System Prompt】强制洗稿规范
# ============================================================================
SYSTEM_PROMPT = """# Role
你是一个顶级的 Manim 架构师与 AI 多模态数据集数据清洗专家。

# Task Objective
你正在将 3b1b 开源库（非 Community 版）中的核心图形类，清洗并封装为"高中物理与数学数据集专用组件库"。
你将接收 3b1b 的原始代码（.py/.md），你的任务是输出一份"洗净"并"打好语义标签"的标准化 Python 组件代码。

# Reference Standard
你需要严格遵守以下"清洗流水线"规范，这是不可违背的红线：

## 0. 【绝对语法红线：抗 ManimCE 污染】（极其重要！！！）
大模型极易混淆 ManimGL (3b1b 原版) 和 ManimCE (社区版) 的语法，你必须严格遵守以下 3b1b 版规则：
- **强制导入规范**：严禁使用 `from manim import ...`！必须且只能使用 `from manimlib import *`。
- **禁止非法初始化参数**：在实例化视觉对象（如 `NumberLine`, `Line`, `Axes`）时，严禁在 `__init__` 中传入 `length`、`width`、`height` 等非标准参数。
- **正确的尺寸修改方式**：如果需要设定长度/宽度，必须先进行基础实例化，然后再调用 `.set_width()` 或 `.set_height()` 方法。例如：`axis = NumberLine(...); axis.set_width(10)`。
- **正确的继承关系**：确保清洗后的类正确继承自 3b1b 源码中的视觉基类（如 `VMobject`, `VGroup`, `CoordinateSystem`），绝对不能断开继承链。

## 1. 净化与降级
- 彻底删除代码中所有与 `checkpoint_paste`、键盘事件、窗口交互相关的代码。
- 移除缺失的本地依赖，使用标准 ManimGL 原生对象进行平替。
- 不使用任何硬编码的本地路径、音频文件、字体文件引用。

## 2. 结构防抖（保障 Bbox 与 ID 追踪）
- 严禁使用透明度为 0 (`Alpha=0`) 的不可见对象来做排版占位，这会产生无用的 Bbox。
- 尽量将图形合并在单一的 `VMobject` 中；如果必须使用 `VGroup`，确保子对象不会在动画初始化时发生 ID 重构。
- 对于复杂的组合图形（如完整的坐标轴带标签），必须被正确封装在统一的父类 `VGroup` 中，确保逻辑上的完整性。

## 3. 强制语义注入（最核心任务）
必须在类的 `__init__` 方法中，注入并初始化以下三个属性，并提供设值接口：

- `self.semantic_type`: 标记视觉类型 (如: "coordinate_system", "function_curve", "geometric_shape")
- `self.semantic_role`: 标记物理/数学含义 (如: "x_axis", "kinematics_curve", "electric_field_line", "gravitational_force")
- `self.semantic_content`: 存储 LaTeX 公式、函数表达式或关键数值 (如: "E = kQ/r^2", "10.5")

属性类型：`self.semantic_type` 和 `self.semantic_role` 必须是字符串；`self.semantic_content` 必须是字符串或 None。

每个属性必须提供 @property getter 和 setter 方法，setter 应该包含基本的类型和值验证。

## 4. 【极其重要】必须重写 copy() 方法！
在返回 `super().copy()` 之后，必须手动将这三个 `semantic_*` 属性赋予新对象，否则动画执行时标签会丢失！
示例代码：
```python
def copy(self, **kwargs) -> 'ClassName':
    new_obj = super().copy(**kwargs)
    new_obj._semantic_type = getattr(self, '_semantic_type', "")
    new_obj._semantic_role = getattr(self, '_semantic_role', "")
    new_obj._semantic_content = getattr(self, '_semantic_content', None)
    return new_obj
```

## 5. 数据集安全方法
确保多次调用 get_bbox() 返回相同结果（除非对象被修改）。

避免因内部结构变化导致的 Bbox 波动。

## 6. 领域快捷封装（加分项）
在类的底部，提供 2-3 个针对高中物理/数学的快捷函数封装。例如，重构 Axes 时提供 KinematicsAxes()，内部自动把 semantic_role 设为 "kinematics_coordinate"。

## 7. 代码输出规范
只输出完整的、符合上述规范的可运行 Python 代码，不要输出任何解释性文字或 Markdown 代码块标记（```python）。

使用 ManimGL 的标准导入路径（from manimlib import *）。

## 8. 类特定的语义预设（根据输入的类名自动适配）
根据接收的原始类名预设标签：

Axes / NumberPlane / ThreeDAxes / ComplexPlane -> semantic_type="coordinate_system"

FunctionGraph / ParametricCurve -> semantic_type="function_curve"

VectorField / StreamLines -> semantic_type="vector_field"

Line / Arrow / Circle / Rectangle / Polygon -> semantic_type="geometric_shape"

Tex / Text / DecimalNumber -> semantic_type="math_formula" 或 "text_label"

# Input & Output
输入：用户发送的具体 3b1b 原始类代码。
输出：直接输出完整的、符合上述规范的可运行 Python 代码，不包含任何解释性文字。
"""


# ============================================================================
# 文件路径配置（动态推导，无硬编码）
# ============================================================================
# 使用 Path(__file__) 动态推导项目根目录
# 脚本位于 scripts/batch_washing_pipeline.py
# parent.parent 指向项目根目录 (3b1b/)
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "extracted_core"
OUTPUT_DIR = BASE_DIR / "washed_manim_components"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_source_files() -> List[Path]:
    """
    获取所有需要清洗的源文件

    优先处理核心类：
    1. 坐标系统类
    2. 函数曲线类
    3. 向量场类
    4. 基础几何与标记类
    5. 文本与公式语义类
    6. 动画类

    使用 Fallback 机制：
    - 优先按照带子目录的模式查找（如 mobject/Axes.py）
    - 如果找不到，递归查找所有子文件夹（如 Axes.py）
    """
    # 定义优先级顺序的文件匹配模式
    priority_patterns = [
        # 坐标系统类（最高优先级）
        ("mobject/Axes", "Axes"),
        ("mobject/NumberPlane", "NumberPlane"),
        ("mobject/ThreeDAxes", "ThreeDAxes"),
        ("mobject/ComplexPlane", "ComplexPlane"),
        ("mobject/CoordinateSystem", "CoordinateSystem"),

        # 函数曲线类
        ("mobject/FunctionGraph", "FunctionGraph"),
        ("mobject/ParametricCurve", "ParametricCurve"),

        # 向量场类
        ("mobject/VectorField", "VectorField"),
        ("mobject/StreamLines", "StreamLines"),
        ("mobject/AnimatedStreamLines", "AnimatedStreamLines"),
        ("mobject/TimeVaryingVectorField", "TimeVaryingVectorField"),

        # 基础几何与标记类
        ("mobject/Line", "Line"),
        ("mobject/DashedLine", "DashedLine"),
        ("mobject/Arrow", "Arrow"),
        ("mobject/Dot", "Dot"),
        ("mobject/Polygon", "Polygon"),
        ("mobject/Circle", "Circle"),
        ("mobject/Rectangle", "Rectangle"),
        ("mobject/Square", "Square"),
        ("mobject/Triangle", "Triangle"),
        ("mobject/RegularPolygon", "RegularPolygon"),
        ("mobject/Ellipse", "Ellipse"),
        ("mobject/TangentLine", "TangentLine"),

        # 文本与公式语义类（可能不在 extracted_core 中，需要 Fallback）
        ("svg/tex_mobject", "Tex"),
        ("svg/text_mobject", "Text"),
        ("numbers", "DecimalNumber"),

        # 动画类
        ("animation/Transform", "Transform"),
        ("animation/ApplyFunction", "ApplyFunction"),
        ("animation/Write", "Write"),
        ("animation/ShowCreation", "ShowCreation"),
    ]

    files = []
    class_names_processed = set()

    # 遍历优先级模式
    for pattern, class_name in priority_patterns:
        # 跳过已处理的类名
        if class_name in class_names_processed:
            continue

        # 方法 1：按照带子目录的模式查找
        py_files = list(SOURCE_DIR.glob(f"{pattern}.py"))

        if py_files:
            files.append(py_files[0])
            class_names_processed.add(class_name)
        else:
            # 方法 2：Fallback - 使用类名递归查找所有子文件夹
            # 使用 rglob 在 SOURCE_DIR 及其所有子文件夹中递归查找
            found_files = list(SOURCE_DIR.rglob(f"{class_name}.py"))

            # 过滤掉 __pycache__ 等临时文件
            valid_files = [
                f for f in found_files
                if "__pycache__" not in str(f)
                and ".pyc" not in str(f)
            ]

            if valid_files:
                # 优先选择最直接路径的文件
                valid_files.sort(key=lambda x: len(str(x)))
                files.append(valid_files[0])
                class_names_processed.add(class_name)
            else:
                # 方法 3：再尝试平铺查找（直接在 SOURCE_DIR 下查找）
                flat_files = list(SOURCE_DIR.glob(f"{class_name}.py"))
                if flat_files:
                    files.append(flat_files[0])
                    class_names_processed.add(class_name)
                else:
                    # 如果都找不到，打印警告但不中断
                    print(f"  ⚠ 警告: 未找到 {class_name} 类文件（可能需要手动提取）")

    return files


def read_source_file(file_path: Path) -> str:
    """读取源文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as read_file:
            return read_file.read()
    except Exception as e:
        print(f"  ✗ 读取文件失败 {file_path}: {str(e)}")
        return None


def wash_class_with_ai(source_code: str, class_name: str) -> str:
    """
    使用 AI 清洗单个类
    移植自 code_gen.py 的 Tabcode 专属 API 逻辑

    Args:
        source_code: 原始代码
        class_name: 类名

    Returns:
        清洗后的代码
    """
    # 构建用户提示词
    user_prompt = f"""请清洗以下 3b1b 的 {class_name} 类代码，严格遵循所有清洗规范。

原始代码：
```
{source_code}
```

请直接输出清洗后的完整 Python 代码，不要包含任何解释性文字、Markdown 标记或代码块符号。代码必须可以直接被 Python 解释器执行。"""

    try:
        # 组装自定义的特殊 payload（Tabcode 专属格式）
        full_content = [
            {"type": "input_text", "text": SYSTEM_PROMPT},
            {"type": "input_text", "text": user_prompt}
        ]

        # 发起特有的流式请求（移植自 code_gen.py）
        resp = client.responses.create(
            model=MODEL_NAME,
            input=[{"role": "user", "content": full_content}],
            stream=True
        )

        # 精准遍历响应流，拼凑最终代码（包含超时保护）
        text = ""
        start = time.time()
        for event in resp:
            # 超时保护：180 秒
            if time.time() - start > 180:
                print("  ⏱ 流式响应超时 (180s)")
                break

            # 提取 delta 文本（Tabcode 专属格式）
            if hasattr(event, "type") and event.type == "response.output_text.delta":
                text += event.delta
                start = time.time()

        return text

    except Exception as e:
        print(f"  ✗ AI 清洗失败: {str(e)}")
        return None


def save_washed_code(output_path: Path, washed_code: str):
    """保存清洗后的代码"""
    with open(output_path, 'w', encoding='utf-8') as write_file:
        write_file.write(washed_code)


def is_already_processed(output_path: Path) -> bool:
    """检查文件是否已经处理过"""
    return output_path.exists()


def get_class_name_from_file(file_path: Path) -> str:
    """从文件路径提取类名"""
    # 从文件名中提取类名（去掉路径和扩展名）
    return file_path.stem


def main():
    """主函数"""
    print("=" * 80)
    print("Manim 核心类批量洗稿脚本（Tabcode 专属 API 版本）")
    print("=" * 80)
    print(f"模型: {MODEL_NAME}")
    print(f"API 端点: {BASE_URL}")
    print(f"项目根目录: {BASE_DIR}")
    print(f"源目录: {SOURCE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print()

    # 检查源目录是否存在
    if not SOURCE_DIR.exists():
        print(f"✗ 源目录不存在: {SOURCE_DIR}")
        print("请确保已经运行 extract_manim_core.py 提取了核心类")
        return

    # 获取所有源文件
    source_files = get_source_files()

    if not source_files:
        print("未找到任何源文件！")
        print("请检查 SOURCE_DIR 路径或运行 extract_manim_core.py")
        return

    print(f"找到 {len(source_files)} 个需要清洗的核心类")
    print()

    # 统计信息
    total = len(source_files)
    success_count = 0
    skip_count = 0
    error_count = 0

    # 遍历每个文件进行清洗
    for file_path in tqdm(source_files, desc="清洗进度"):
        class_name = get_class_name_from_file(file_path)
        output_path = OUTPUT_DIR / f"Washed_{class_name}.py"

        # 断点续洗：检查是否已经处理过
        if is_already_processed(output_path):
            print(f"  ⊘ {class_name} - 已存在，跳过")
            skip_count += 1
            continue

        # 读取源代码
        source_code = read_source_file(file_path)

        if source_code is None:
            error_count += 1
            continue

        # 使用 AI 清洗
        print(f"\n  正在清洗: {class_name}")
        print(f"  源文件: {file_path.relative_to(BASE_DIR)}")
        washed_code = wash_class_with_ai(source_code, class_name)

        if washed_code is None:
            error_count += 1
            # 保存错误标记文件
            error_path = OUTPUT_DIR / f"ERROR_{class_name}.txt"
            save_washed_code(error_path, f"清洗失败\n\n原始代码:\n{source_code}")
            continue

        # 验证输出是否有效
        if not washed_code.strip() or len(washed_code) < 100:
            print(f"  ✗ {class_name} - 输出无效或过短")
            error_count += 1
            # 保存错误标记文件
            error_path = OUTPUT_DIR / f"ERROR_{class_name}.txt"
            save_washed_code(error_path, f"输出无效\n\n原始代码:\n{source_code}\n\nAI 输出:\n{washed_code}")
            continue

        # 保存清洗后的代码
        try:
            save_washed_code(output_path, washed_code)
            print(f"  ✓ {class_name} - 清洗完成 ({len(washed_code)} 字符)")
            success_count += 1

            # 添加延迟以避免 API 限流
            time.sleep(1)

        except Exception as e:
            print(f"  ✗ {class_name} - 保存失败: {str(e)}")
            error_count += 1

    # 打印统计信息
    print()
    print("=" * 80)
    print("洗稿完成！统计信息：")
    print("=" * 80)
    print(f"总文件数: {total}")
    print(f"成功清洗: {success_count}")
    print(f"跳过文件: {skip_count}")
    print(f"失败文件: {error_count}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 80)


# ============================================================================
# 【修复】正确的入口判断
# ============================================================================
if __name__ == "__main__":
    main()
