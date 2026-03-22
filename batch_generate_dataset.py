#!/usr/bin/env python3
"""
批量生成数据集脚本 - 遍历整个 3b1b 源码仓库生成训练数据

================================================================================
前置说明：如何重构之前的单文件脚本以支持模块化导入
================================================================================

1. static_code_parser.py 的重构（已就绪，无需修改）：
   - 已有 parse_file(file_path: str, output_format: str) -> str 函数
   - 可以直接 import 使用

2. format_to_jsonl.py 的重构（需要微调）：
   当前脚本使用类结构，建议在文件末尾添加以下函数：

   ```python
   def convert_to_jsonl_lines(ast_data: Dict[str, Any]) -> List[str]:
       \"\"\"
       将 AST 数据转换为 JSONL 行列表

       Args:
           ast_data: AST 解析器输出的字典数据

       Returns:
           JSONL 字符串列表
       \"\"\"
       formatter = JSONLFormatter()
       formatter.jsonl_records = []
       formatter.known_objects = set()

       for class_name, scene_data in ast_data.get("scenes", {}).items():
           formatter.known_objects.clear()

           animation_steps = scene_data.get("animation_steps", [])
           for step in animation_steps:
               record = formatter._generate_record(class_name, step)
               formatter.jsonl_records.append(record)

       # 生成 JSONL 字符串列表
       jsonl_lines = []
       for record in formatter.jsonl_records:
           json_str = json.dumps(record, ensure_ascii=False)
           jsonl_lines.append(json_str)

       return jsonl_lines
   ```

   如果不想修改 format_to_jsonl.py，本脚本提供了适配器层来兼容当前结构。

================================================================================
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 尝试导入 tqdm，如果没有安装则使用简单的进度打印
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# 导入自定义模块
from static_code_parser import parse_file
from format_to_jsonl import convert_to_jsonl_lines


class BatchDatasetGenerator:
    """批量数据集生成器"""

    def __init__(
        self,
        source_dir: str = "videos-master",
        output_file: str = "master_dataset.jsonl",
        error_log: str = "batch_error.log"
    ):
        """
        初始化批量生成器

        Args:
            source_dir: 源码目录路径
            output_file: 输出的 JSONL 文件路径
            error_log: 错误日志文件路径
        """
        self.source_dir = Path(source_dir)
        self.output_file = Path(output_file)
        self.error_log = Path(error_log)

        # 统计信息
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_records": 0
        }

    def run(self) -> None:
        """
        执行批量生成流程
        """
        print("=" * 70)
        print("开始批量生成数据集")
        print(f"源码目录: {self.source_dir.absolute()}")
        print(f"输出文件: {self.output_file.absolute()}")
        print(f"错误日志: {self.error_log.absolute()}")
        print("=" * 70)
        print()

        # 检查源码目录是否存在
        if not self.source_dir.exists():
            print(f"错误：源码目录不存在: {self.source_dir}")
            return

        # 清空或创建输出文件
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("")  # 清空文件

        # 清空错误日志
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.error_log, 'w', encoding='utf-8') as f:
            f.write(f"批量生成错误日志 - {datetime.now()}\n")
            f.write("=" * 70 + "\n\n")

        # 获取所有 Python 文件
        py_files = list(self.source_dir.rglob('*.py'))
        self.stats["total"] = len(py_files)

        if self.stats["total"] == 0:
            print("警告：没有找到任何 Python 文件")
            return

        print(f"找到 {self.stats['total']} 个 Python 文件\n")

        # 使用 tqdm 或普通循环处理文件
        file_iter = py_files
        if TQDM_AVAILABLE:
            file_iter = tqdm(py_files, desc="解析进度", unit="file")

        for py_file in file_iter:
            self._process_file(py_file)

        # 输出统计信息
        self._print_summary()

    def _process_file(self, py_file: Path) -> None:
        """
        处理单个 Python 文件

        Args:
            py_file: Python 文件路径
        """
        try:
            # 调用 AST 解析器
            ast_json_str = parse_file(str(py_file), output_format="json")

            # 检查是否返回了错误
            if '"error":' in ast_json_str:
                error_data = json.loads(ast_json_str)
                raise ValueError(error_data.get("error", "未知错误"))

            # 解析 AST JSON
            ast_data = json.loads(ast_json_str)

            # 转换为 JSONL 行
            jsonl_lines = convert_to_jsonl_lines(ast_data)

            # 写入输出文件（追加模式）
            if jsonl_lines:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    for line in jsonl_lines:
                        f.write(line + '\n')

                self.stats["success"] += 1
                self.stats["total_records"] += len(jsonl_lines)
            else:
                # 文件成功解析但没有生成记录（可能没有 Scene 类）
                self.stats["success"] += 1

        except Exception as e:
            # 捕获异常并记录到错误日志
            self.stats["failed"] += 1
            self._log_error(py_file, e)

    def _log_error(self, py_file: Path, error: Exception) -> None:
        """
        记录错误到日志文件

        Args:
            py_file: 出错的文件路径
            error: 异常对象
        """
        error_msg = f"\n文件: {py_file}\n"
        error_msg += f"错误类型: {type(error).__name__}\n"
        error_msg += f"错误信息: {str(error)}\n"
        error_msg += "-" * 70 + "\n"

        # 追加写入错误日志
        with open(self.error_log, 'a', encoding='utf-8') as f:
            f.write(error_msg)

        # 控制台输出简短错误信息
        print(f"错误处理: {py_file.name} - {type(error).__name__}: {str(error)[:50]}")

    def _print_summary(self) -> None:
        """
        打印统计摘要
        """
        print("\n" + "=" * 70)
        print("批量生成完成")
        print("=" * 70)
        print(f"总文件数: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失败: {self.stats['failed']}")
        print(f"成功率: {self.stats['success'] / self.stats['total'] * 100:.1f}%")
        print(f"总记录数: {self.stats['total_records']}")
        print("=" * 70)

        if self.stats['failed'] > 0:
            print(f"\n有 {self.stats['failed']} 个文件处理失败，请查看错误日志: {self.error_log}")


def main():
    """
    主函数
    """
    # 配置参数（可修改）
    SOURCE_DIR = "/Users/chenshutong/Desktop/3b1b/videos-master"
    OUTPUT_FILE = "master_dataset.jsonl"
    ERROR_LOG = "batch_error.log"

    # 创建生成器并运行
    generator = BatchDatasetGenerator(
        source_dir=SOURCE_DIR,
        output_file=OUTPUT_FILE,
        error_log=ERROR_LOG
    )
    generator.run()


if __name__ == "__main__":
    main()
