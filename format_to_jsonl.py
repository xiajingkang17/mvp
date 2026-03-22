#!/usr/bin/env python3
"""将 AST 解析结果格式化为 Vision Agent 训练用 JSONL。"""

import json
from typing import Dict, Any, List
from pathlib import Path

from static_layout_solver import solve_ast_dataset


def convert_to_jsonl_lines(ast_data: Dict[str, Any]) -> List[str]:
    """
    将 AST 数据转换为 JSONL 行列表（对外暴露的函数接口）

    Args:
        ast_data: AST 解析器输出的字典数据

    Returns:
        JSONL 字符串列表
    """
    return [json.dumps(record, ensure_ascii=False) for record in solve_ast_dataset(ast_data)]


class JSONLFormatter:
    """保留旧接口，内部直接委托给新的静态布局求解器。"""

    def convert(self, ast_json_path: str, output_path: str) -> None:
        with open(ast_json_path, 'r', encoding='utf-8') as f:
            ast_data = json.load(f)

        jsonl_lines = convert_to_jsonl_lines(ast_data)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in jsonl_lines:
                f.write(line + '\n')

        print(f"成功生成 {len(jsonl_lines)} 条 JSONL 记录")
        print(f"输出文件: {output_path}")


def main():
    """
    主函数：将 AST 解析器输出转换为 JSONL 格式
    """
    # 配置路径
    ast_json_path = "ast_output.json"  # AST 解析器输出的 JSON 文件
    output_path = "dataset.jsonl"     # 输出的 JSONL 文件

    # 检查输入文件是否存在
    if not Path(ast_json_path).exists():
        print(f"错误：找不到输入文件 {ast_json_path}")
        print("请先运行 static_code_parser.py 生成 ast_output.json")
        return

    # 创建格式化器并执行转换
    formatter = JSONLFormatter()
    formatter.convert(ast_json_path, output_path)


if __name__ == "__main__":
    main()
