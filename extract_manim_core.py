#!/usr/bin/env python3
"""
Manim Core Extractor - AST Analysis Script

该脚本用于提取 Manim 核心模块中的类定义、方法和文档字符串。
目标目录：
  - manimlib/mobject/ (geometry.py, vector_field.py, functions.py, coordinate_systems.py)
  - manimlib/animation/ (creation.py, transform.py)

输出：每个类的定义会被提取到独立的 .py 文件中
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any


class ClassExtractor(ast.NodeVisitor):
    """提取类定义的 AST 访问器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.classes: List[Dict[str, Any]] = []
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """访问类定义节点"""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'bases': [ast.unparse(base) for base in node.bases],
            'methods': [],
            'attributes': [],
            'linenumber': node.lineno,
        }

        # 提取方法和属性
        self.current_class = class_info
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    'name': item.name,
                    'docstring': ast.get_docstring(item),
                    'args': [arg.arg for arg in item.args.args],
                    'returns': ast.unparse(item.returns) if item.returns else None,
                    'linenumber': item.lineno,
                    'decorators': [ast.unparse(dec) for dec in item.decorator_list],
                    'is_property': any(isinstance(d, ast.Name) and d.id == 'property' for d in item.decorator_list),
                }
                class_info['methods'].append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info['attributes'].append({
                            'name': target.id,
                            'value': ast.unparse(item.value),
                        })

        self.classes.append(class_info)
        self.current_class = None


def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """分析单个 Python 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=file_path)
        extractor = ClassExtractor(file_path)
        extractor.visit(tree)
        return extractor.classes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def generate_class_document(class_info: Dict[str, Any], source_file: str) -> str:
    """生成类的文档字符串"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"Class: {class_info['name']}")
    lines.append(f"Source: {source_file}:{class_info['linenumber']}")
    lines.append("=" * 80)
    lines.append("")

    if class_info['docstring']:
        lines.append("Documentation:")
        lines.append("-" * 40)
        lines.append(class_info['docstring'])
        lines.append("")

    if class_info['bases']:
        lines.append("Inherits from:")
        lines.append(f"  {', '.join(class_info['bases'])}")
        lines.append("")

    if class_info['attributes']:
        lines.append("Class Attributes:")
        lines.append("-" * 40)
        for attr in class_info['attributes']:
            lines.append(f"  {attr['name']} = {attr['value']}")
        lines.append("")

    if class_info['methods']:
        lines.append("Methods:")
        lines.append("-" * 40)
        for method in class_info['methods']:
            lines.append("")
            lines.append(f"  Method: {method['name']}")
            if method['decorators']:
                lines.append(f"    Decorators: {', '.join(method['decorators'])}")
            if method['is_property']:
                lines.append("    @property")
            args = ", ".join(method['args'][1:])  # Skip 'self'
            if method['returns']:
                lines.append(f"    def {method['name']}({args}) -> {method['returns']}")
            else:
                lines.append(f"    def {method['name']}({args})")
            if method['docstring']:
                lines.append("")
                for line in method['docstring'].split('\n'):
                    lines.append(f"      {line}")
            lines.append(f"    Source line: {method['linenumber']}")
        lines.append("")

    return "\n".join(lines)


def generate_class_code_stub(class_info: Dict[str, Any]) -> str:
    """生成类代码片段（简化版，保留结构）"""
    lines = []

    # 类定义行
    bases = ", ".join(class_info['bases']) if class_info['bases'] else ""
    if bases:
        lines.append(f"class {class_info['name']}({bases}):")
    else:
        lines.append(f"class {class_info['name']}:")

    # 文档字符串
    if class_info['docstring']:
        lines.append('    """')
        for line in class_info['docstring'].split('\n'):
            lines.append(f"    {line}")
        lines.append('    """')

    # 属性
    for attr in class_info['attributes']:
        lines.append(f"    {attr['name']} = {attr['value']}")

    # 方法
    for method in class_info['methods']:
        lines.append("")

        # 装饰器
        for dec in method['decorators']:
            lines.append(f"    @{dec}")

        # 方法定义
        args = ", ".join(method['args'])
        if method['returns']:
            lines.append(f"    def {method['name']}({args}) -> {method['returns']}:")
        else:
            lines.append(f"    def {method['name']}({args}):")

        # 方法文档字符串
        if method['docstring']:
            lines.append('        """')
            for line in method['docstring'].split('\n'):
                lines.append(f"        {line}")
            lines.append('        """')
        else:
            lines.append("        pass")

    return "\n".join(lines)


def main():
    """主函数"""
    # Manim 核心文件路径
    manim_base = Path("/Users/chenshutong/Desktop/Manim_Dataset_Test/manim-master")
    output_dir = Path("/Users/chenshutong/Desktop/3b1b/extracted_core")

    # 定义要提取的目标文件
    target_files = [
        "manimlib/mobject/geometry.py",
        "manimlib/mobject/vector_field.py",
        "manimlib/mobject/functions.py",
        "manimlib/mobject/coordinate_systems.py",
        "manimlib/animation/creation.py",
        "manimlib/animation/transform.py",
    ]

    print("=" * 80)
    print("Manim Core Extractor")
    print("=" * 80)
    print(f"Output directory: {output_dir}")
    print("")

    # 创建输出目录结构
    for category in ["mobject", "animation"]:
        (output_dir / category).mkdir(parents=True, exist_ok=True)

    total_classes = 0

    for relative_path in target_files:
        full_path = manim_base / relative_path

        if not full_path.exists():
            print(f"WARNING: File not found: {full_path}")
            continue

        print(f"Processing: {relative_path}")
        classes = analyze_file(str(full_path))

        if not classes:
            print(f"  No classes found in {relative_path}")
            continue

        # 确定输出类别
        if "mobject" in relative_path:
            category = "mobject"
        elif "animation" in relative_path:
            category = "animation"
        else:
            category = "other"

        # 为每个类生成文档和代码片段
        file_base = Path(relative_path).stem

        for class_info in classes:
            total_classes += 1
            safe_class_name = class_info['name'].replace("<", "").replace(">", "")

            # 生成文档文件
            doc_path = output_dir / category / f"{safe_class_name}.md"
            doc_content = generate_class_document(class_info, relative_path)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)

            # 生成代码片段文件
            code_path = output_dir / category / f"{safe_class_name}.py"
            code_content = generate_class_code_stub(class_info)
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(code_content)

        print(f"  Extracted {len(classes)} classes")

    print("")
    print("=" * 80)
    print(f"Extraction complete! Total classes extracted: {total_classes}")
    print(f"Output directory: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
