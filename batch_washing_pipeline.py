#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3b1b 组件语义注入洗稿流水线

功能：
1. 定位需要语义增强的 3b1b 基础组件类
2. 通过 AI 劫持重写，强制注入 self.semantic_role 和 self.semantic_content
3. 保持原有 manimlib 继承结构和参数完整性
4. 生成具备强语义的增强版组件库
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import logging
from openai import OpenAI

# ==================== OpenAI API 配置 ====================

# 强制加载根目录下的 .env 文件
from dotenv import load_dotenv
env_path = Path("/Users/chenshutong/Desktop/3b1b/.env")
load_dotenv(dotenv_path=env_path)

# 从环境变量读取配置
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.tabcode.cc/openai")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4")

if not API_KEY:
    raise ValueError("❌ 未找到 OPENAI_API_KEY，请检查 /Users/chenshutong/Desktop/3b1b/.env 文件是否配置正确！")

# 初始化 OpenAI 客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=180.0)

# ==================== 全局配置 ====================

# 3b1b 核心组件库根目录
SOURCE_DIR = Path("/Users/chenshutong/Desktop/3b1b/extracted_core")

# 自定义组件目录（通常包含基础的 MObject 类定义）
CUSTOM_DIR = SOURCE_DIR / "custom"

# 输出目录（洗稿后的增强版组件）
OUTPUT_DIR = Path("/Users/chenshutong/Desktop/3b1b/washed_manim_components")

# 日志配置
LOG_FILE = Path("/Users/chenshutong/Desktop/3b1b/washing_log.txt")

# ==================== 待处理的组件队列 ====================

# 核心基础组件，按优先级排序
PRIORITY_COMPONENTS = [
    "Tex",              # 数学公式组件（优先级最高）
    "Text",             # 文本组件
    "Square",           # 正方形几何组件
    "Circle",           # 圆形几何组件
    "Dot",              # 点组件
]

# 扩展组件队列（可根据需要补充）
EXTENDED_COMPONENTS = [
    "Vector",           # 向量组件
    "Line",             # 线条组件
    "Rectangle",        # 矩形组件
    "Triangle",         # 三角形组件
    "Axes",            # 坐标轴组件
    "NumberPlane",      # 数字平面组件
    "ComplexPlane",     # 复平面组件
    "Arrow",           # 箭头组件
    "Group",           # 组合对象
    "VGroup",          # 垂直组合对象
]

# ==================== 日志配置 ====================

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== 组件定位功能 ====================

def get_source_files() -> list:
    """
    获取待处理的源文件列表，按照优先级组件队列精确匹配

    Returns:
        包含 (文件路径, 组件名) 的列表
    """
    # 极其精确的 5 个目标组件匹配规则
    priority_patterns = [
        ("mobject/Square", "Square"),
        ("mobject/Circle", "Circle"),
        ("mobject/Dot", "Dot"),
        ("mobject/tex_mobject", "Tex"),  # 极其重要：3b1b 早期大量使用的是 Tex
        ("mobject/text_mobject", "Text"),  # 文本组件
    ]

    source_files = []

    for path_pattern, component_name in priority_patterns:
        # 在 mobject 目录中直接搜索匹配的文件
        search_path = SOURCE_DIR / "mobject"
        for py_file in search_path.glob(f"*.py"):
            if path_pattern in str(py_file.relative_to(SOURCE_DIR)):
                logger.info(f"✓ 找到优先组件 {component_name}: {py_file}")
                source_files.append((py_file, component_name))
                break  # 每个组件只取第一个匹配文件

    return source_files

def locate_component_file(component_name: str) -> Path:
    """
    在源码目录中定位指定组件的定义文件

    Args:
        component_name: 组件类名（如 "Tex", "Square"）

    Returns:
        组件文件的完整路径，如果找不到则返回 None
    """
    # 搜索策略：
    # 1. 先在 custom 目录搜索
    # 2. 再在整个源码目录递归搜索
    # 3. 查找包含 "class {component_name}" 的文件

    search_patterns = [
        f"class {component_name}(",
        f"class {component_name} (",
    ]

    for pattern in search_patterns:
        # 搜索 custom 目录
        custom_files = list(SOURCE_DIR.rglob(f"*.py"))
        for py_file in custom_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if pattern in content:
                        logger.info(f"✓ 找到组件 {component_name}: {py_file}")
                        return py_file
            except Exception as e:
                continue

    logger.warning(f"⚠ 未找到组件 {component_name}")
    return None

def extract_component_class(content: str, component_name: str) -> str:
    """
    从文件内容中提取指定组件类的完整代码

    Args:
        content: Python 文件内容
        component_name: 组件类名

    Returns:
        组件类的完整代码字符串
    """
    # 提取从 "class ComponentName" 到下一个 class 定义或文件结尾
    lines = content.split('\n')
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if f"class {component_name}" in line:
            start_idx = i
        elif start_idx is not None and line.strip().startswith('class ') and i > start_idx:
            end_idx = i
            break

    if start_idx is not None:
        if end_idx is None:
            class_code = '\n'.join(lines[start_idx:])
        else:
            class_code = '\n'.join(lines[start_idx:end_idx])
        return class_code

    return None

# ==================== AI 洗稿功能 ====================

def wash_class_with_ai(source_code: str, class_name: str) -> str:
    """
    使用 AI 清洗单个类 (真实调用版)
    """
    # 系统提示词
    SYSTEM_PROMPT = """
你是一位专业的 3D 动画组件语义增强专家。你的任务是为 3b1b（3Blue1Brown）视频项目的 ManimGL 组件添加强语义属性。

## 核心要求

你在重写组件时，必须在 __init__ 方法中强制注入以下两个属性：

1. **self.semantic_role**: 组件的语义角色，例如：
   - 'math_equation' - 数学公式
   - 'variable' - 数学变量
   - 'constant' - 数学常数
   - 'geometric_shape' - 几何图形
   - 'coordinate_axis' - 坐标轴
   - 'vector' - 向量/箭头
   - 'text_label' - 文本标签
   - 'point_marker' - 点标记
   - 'visual_element' - 通用视觉元素

2. **self.semantic_content**: 组件的语义内容，必须提取：
   - 对于 Tex/TextMobject：提取传入的 LaTeX 字符串或纯文本
   - 对于几何组件：提取形状类型和尺寸信息
   - 对于向量组件：提取方向和大小信息
   - 对于组合组件：描述包含的子元素

## 绝对禁止

- 绝对不能破坏原有的 manimlib 继承关系
- 绝对不能修改原有的参数接口
- 绝对不能删除或重命名已有的属性
- 绝对不能破坏现有的渲染逻辑

## 输出格式

返回完整的重写代码，包含增强后的 __init__ 方法。确保代码可以直接替换原组件文件，无需任何额外修改。

## 示例增强

对于 Tex 组件，原 __init__ 可能是：
```python
def __init__(self, tex_string, **kwargs):
    super().__init__(tex_string, **kwargs)
```

增强后的版本应该是：
```python
def __init__(self, tex_string, **kwargs):
    super().__init__(tex_string, **kwargs)
    self.semantic_role = 'math_equation'
    self.semantic_content = tex_string
```

现在请根据组件的实际实现，进行智能语义注入。
"""

    user_prompt = f"请清洗以下 3b1b 的 {class_name} 类代码，严格遵循所有清洗规范。\n\n原始代码：\n```\n{source_code}\n```\n\n请直接输出清洗后的完整 Python 代码，不要包含任何解释性文字、Markdown 标记或代码块符号。"

    try:
        # 组装自定义的特殊 payload（Tabcode 专属格式）
        full_content = [
            {"type": "input_text", "text": SYSTEM_PROMPT},
            {"type": "input_text", "text": user_prompt}
        ]

        print(f"    ▶ 正在请求 AI 处理 {class_name}...")
        # 发起特有的流式请求
        resp = client.responses.create(
            model=MODEL_NAME,
            input=[{"role": "user", "content": full_content}],
            stream=True
        )

        # 精准遍历响应流，拼凑最终代码（包含超时保护）
        text = ""
        import time
        start = time.time()
        for event in resp:
            if time.time() - start > 180:
                print("    ⏱ 流式响应超时 (180s)")
                break
            if hasattr(event, "type") and event.type == "response.output_text.delta":
                text += event.delta
                start = time.time()

        return text

    except Exception as e:
        print(f"    ✗ AI 清洗失败: {str(e)}")
        return None

# ==================== 文件处理功能 ====================

def process_single_component(component_name: str) -> bool:
    """
    处理单个组件：定位、提取、洗稿、保存

    Args:
        component_name: 组件类名

    Returns:
        处理是否成功
    """
    try:
        # 1. 定位组件文件
        component_file = locate_component_file(component_name)
        if not component_file:
            return False

        # 2. 读取文件内容
        with open(component_file, 'r', encoding='utf-8') as f:
            original_code = f.read()

        # 3. 提取组件类代码
        component_code = extract_component_class(original_code, component_name)
        if not component_code:
            logger.error(f"✗ 无法提取组件 {component_name} 的代码")
            return False

        # 4. AI 洗稿
        enhanced_code = wash_class_with_ai(component_code, component_name)

        # 5. 保存增强版组件
        output_file = OUTPUT_DIR / f"enhanced_{component_name.lower()}.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_code)

        logger.info(f"✓ 组件 {component_name} 洗稿完成，保存至：{output_file}")
        return True

    except Exception as e:
        logger.error(f"✗ 处理组件 {component_name} 失败：{e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

# ==================== 批量处理功能 ====================

def process_batch_components(component_list: list) -> dict:
    """
    批量处理组件列表，优先使用精准文件匹配

    Args:
        component_list: 组件名称列表

    Returns:
        处理结果统计
    """
    # 优先使用精准的文件匹配
    source_files = get_source_files()

    if source_files:
        logger.info(f"\n🚀 开始批量洗稿 {len(source_files)} 个精准匹配的组件...")
    else:
        logger.info(f"\n🚀 开始批量洗稿 {len(component_list)} 个组件...")

    results = {
        'total': len(source_files) if source_files else len(component_list),
        'success': 0,
        'failed': 0,
        'components': []
    }

    # 如果有精准匹配的文件，优先处理这些
    if source_files:
        for file_path, component_name in source_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"处理组件：{component_name} ({file_path.name})")
            logger.info(f"{'='*60}")

            if process_single_component(component_name):
                results['success'] += 1
                results['components'].append({
                    'name': component_name,
                    'file': str(file_path),
                    'status': 'success'
                })
            else:
                results['failed'] += 1
                results['components'].append({
                    'name': component_name,
                    'file': str(file_path),
                    'status': 'failed'
                })
    else:
        # 如果没有精准匹配，则回退到按组件名处理
        for component_name in component_list:
            logger.info(f"\n{'='*60}")
            logger.info(f"处理组件：{component_name}")
            logger.info(f"{'='*60}")

            if process_single_component(component_name):
                results['success'] += 1
                results['components'].append({
                    'name': component_name,
                    'status': 'success'
                })
            else:
                results['failed'] += 1
                results['components'].append({
                    'name': component_name,
                    'status': 'failed'
                })

    return results

def generate_washing_report(results: dict):
    """生成洗稿报告"""
    report = f"""
╔═══════════════════════════════════════════════════════════╗
║              3b1b 组件语义注入洗稿完成报告                     ║
╠═══════════════════════════════════════════════════════════╣
║  处理组件总数：{results['total']:<40} ║
║  成功增强：   {results['success']:<40} ║
║  处理失败：   {results['failed']:<40} ║
╠═══════════════════════════════════════════════════════════╣
║  输出目录：                                         ║
║    {str(OUTPUT_DIR)[:40]:<45} ║
║  日志文件：                                         ║
║    {str(LOG_FILE)[:40]:<45} ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(report)

    # 保存详细的 JSON 格式报告
    report_file = OUTPUT_DIR / "washing_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"📄 详细报告已保存至：{report_file}")

# ==================== 主程序 ====================

def main():
    """主程序入口"""
    logger.info("="*70)
    logger.info("🧼 3b1b 组件语义注入洗稿流水线")
    logger.info("="*70)

    try:
        # 准备输出目录
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 处理优先级组件
        logger.info("\n📋 优先处理核心基础组件：")
        for i, component in enumerate(PRIORITY_COMPONENTS, 1):
            logger.info(f"  {i}. {component}")

        priority_results = process_batch_components(PRIORITY_COMPONENTS)
        generate_washing_report(priority_results)

        # 询问是否处理扩展组件
        logger.info("\n⚠️  扩展组件队列已就绪，包含以下组件：")
        for i, component in enumerate(EXTENDED_COMPONENTS, 1):
            logger.info(f"  {i}. {component}")

        logger.info("\n✅ 优先组件洗稿完成！")
        logger.info("💡 提示：如需处理扩展组件，请修改 PRIORITY_COMPONENTS 列表")

    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断程序执行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序执行失败：{e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
