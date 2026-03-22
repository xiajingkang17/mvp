#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件端到端测试脚本

功能：
1. 劫持单个 3b1b 源文件
2. 替换 Scene 类为 DataGenScene
3. 调用 manimgl 静默渲染
4. 验证输出的 JSONL 格式是否正确
"""

import re
import subprocess
import sys
import logging
from pathlib import Path
import json
import time

# ==================== 全局配置 ====================

# 测试目标文件（硬编码）
TEST_FILE = Path("/Users/chenshutong/Desktop/3b1b/videos-master/_2015/complex_multiplication_article.py")

# 临时修改后的代码存放目录
TEMP_RUN_DIR = Path("/Users/chenshutong/Desktop/Temp_Hacked_Scenes")

# 数据输出目录
OUTPUT_DIR = Path("/Users/chenshutong/Desktop/Manim_Dataset_Output")
OUTPUT_FILE = OUTPUT_DIR / "dataset.jsonl"

# ManimGL 渲染命令
MANIM_CMD = "manimgl"

# 日志配置
LOG_FILE = Path("/Users/chenshutong/Desktop/3b1b/test_single_log.txt")

# ==================== 正则表达式配置 ====================

# 匹配 class XXX(...Scene...): 的定义
SCENE_CLASS_PATTERN = re.compile(
    r'class\s+(\w+)\s*\(\s*([^)]*Scene[^)]*)\s*\):',
    re.MULTILINE
)

# 检查文件是否已包含 DataGenScene 导入
DATAGEN_IMPORT_PATTERN = re.compile(
    r'from\s+data_gen_base\s+import\s+DataGenScene',
    re.MULTILINE
)

# 检查文件是否已经过劫持（包含标记）
HACKED_MARK_PATTERN = re.compile(
    r'#\s*HACKED_BY_DATA_GEN_SCRIPT',
    re.MULTILINE
)

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

# ==================== 核心功能函数 ====================

def ensure_directories():
    """确保所有必要的目录都存在"""
    TEMP_RUN_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ 目录准备完成")

def extract_scene_classes(content: str):
    """
    从代码内容中提取所有场景类名

    Args:
        content: Python 文件内容

    Returns:
        场景类名列表
    """
    matches = SCENE_CLASS_PATTERN.findall(content)
    class_names = [match[0] for match in matches]
    return class_names

def hijack_scene_file(source_file: Path, output_dir: Path):
    """
    劫持一个 Scene 文件，将其转换为 DataGenScene 子类

    Args:
        source_file: 源文件路径
        output_dir: 输出目录

    Returns:
        (劫持后的文件路径, 提取的场景类名列表)
    """
    try:
        # 读取源文件内容
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有场景类名
        scene_classes = extract_scene_classes(content)

        if not scene_classes:
            logger.warning(f"文件不包含 Scene 类，跳过：{source_file}")
            return None, []

        # 检查是否已经劫持过
        if HACKED_MARK_PATTERN.search(content):
            logger.warning(f"文件已劫持过，跳过：{source_file}")
            return None, []

        logger.info(f"发场景类：{', '.join(scene_classes)}")

        # 执行劫持操作
        hacked_content = content

        # 1. 在文件头部添加劫持标记和导入语句
        import_statement = '\n# HACKED_BY_DATA_GEN_SCRIPT\nfrom data_gen_base import DataGenScene\n'

        # 找到第一个有效的导入语句或文档字符串后的位置
        lines = hacked_content.split('\n')
        insert_pos = 0

        # 跳过文件开头的 shebang 和编码声明
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#!'):
                insert_pos = i + 1
            elif stripped.startswith('# -*-'):
                insert_pos = i + 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                # 跳过文档字符串
                insert_pos = i + 1
                if len(stripped) > 3:  # 单行文档字符串
                    insert_pos = i + 1
                else:  # 多行文档字符串
                    for j in range(i + 1, len(lines)):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            insert_pos = j + 1
                            break
                break
            elif stripped and not stripped.startswith('#'):
                # 找到第一个非注释、非空行，在此之前插入
                insert_pos = i
                break

        # 插入劫持标记和导入语句
        lines.insert(insert_pos, import_statement)
        hacked_content = '\n'.join(lines)

        # 2. 替换所有 Scene 继承为 DataGenScene
        # 使用正则替换：class XXX(...Scene...) -> class XXX(DataGenScene)
        hacked_content = SCENE_CLASS_PATTERN.sub(r'class \1(DataGenScene):', hacked_content)

        # 3. 确定输出文件路径
        output_file = output_dir / source_file.name

        # 保存劫持后的代码
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(hacked_content)

        logger.info(f"✓ 劫持完成：{source_file.name} -> {output_file.name}")
        return output_file, scene_classes

    except Exception as e:
        logger.error(f"✗ 劫持失败 {source_file}：{e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None, []

def render_hacked_scene(hacked_file: Path, scene_class: str) -> bool:
    """
    使用 manimgl 在后台静默渲染劫持后的场景

    Args:
        hacked_file: 劫持后的 Python 文件路径
        scene_class: 要渲染的场景类名

    Returns:
        渲染是否成功
    """
    try:
        # 构建渲染命令
        cmd = [
            MANIM_CMD,
            str(hacked_file),
            scene_class,
            '--skip_animations',  # 跳过动画，只触发数据抓取
            '--quality', 'l',  # 低质量，加快渲染速度
            '--disable_caching',  # 禁用缓存
        ]

        logger.info(f"▶ 开始渲染：{scene_class}")

        # 在后台执行渲染命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 超时时间：5分钟
            cwd=TEMP_RUN_DIR.parent  # 工作目录
        )

        if result.returncode == 0:
            logger.info(f"✓ 渲染成功：{scene_class}")
            return True
        else:
            logger.warning(f"⚠ 渲染失败：{scene_class}")
            logger.warning(f"  错误输出：{result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        logger.warning(f"⏱ 渲染超时：{scene_class}")
        return False
    except Exception as e:
        logger.error(f"✗ 渲染异常 {scene_class}：{e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def validate_jsonl_output() -> dict:
    """
    验证 JSONL 输出格式是否正确

    Returns:
        验证结果字典
    """
    validation_results = {
        'file_exists': False,
        'total_lines': 0,
        'valid_json_lines': 0,
        'bbox_in_range': True,
        'bbox_errors': [],
        'status_valid': True,
        'status_errors': [],
        'id_format_valid': True,
        'id_errors': [],
        'sample_data': []
    }

    if not OUTPUT_FILE.exists():
        logger.error(f"✗ JSONL 文件不存在：{OUTPUT_FILE}")
        return validation_results

    validation_results['file_exists'] = True

    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        validation_results['total_lines'] = len(lines)

        # 读取最后几行进行分析
        sample_lines = lines[-10:] if len(lines) >= 10 else lines

        for line in sample_lines:
            try:
                data = json.loads(line.strip())
                validation_results['valid_json_lines'] += 1

                # 检查 bbox 是否在 [0, 1] 范围内
                if 'bbox' in data and data['bbox'] is not None:
                    bbox = data['bbox']
                    if isinstance(bbox, list) and len(bbox) == 6:
                        for coord in bbox:
                            if not (0 <= coord <= 1):
                                validation_results['bbox_in_range'] = False
                                validation_results['bbox_errors'].append({
                                    'id': data.get('id', 'unknown'),
                                    'bbox': bbox,
                                    'invalid_coord': coord
                                })
                                break

                # 检查 status 字段
                if 'status' in data:
                    if data['status'] not in ['keep', 'new', 'error']:
                        validation_results['status_valid'] = False
                        validation_results['status_errors'].append({
                            'id': data.get('id', 'unknown'),
                            'invalid_status': data['status']
                        })

                # 检查 id 字段格式（类名_内存地址）
                if 'id' in data:
                    id_str = data['id']
                    # 检查格式是否为 类名_数字
                    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*_\d+$', id_str):
                        validation_results['id_format_valid'] = False
                        validation_results['id_errors'].append({
                            'id': id_str,
                            'reason': 'Format does not match ClassName_MemoryAddress'
                        })

                validation_results['sample_data'].append(data)

            except json.JSONDecodeError as e:
                logger.warning(f"⚠ JSON 解析失败：{e}")

    except Exception as e:
        logger.error(f"✗ 验证 JSONL 失败：{e}")

    return validation_results

def print_validation_report(results: dict):
    """
    打印验证报告

    Args:
        results: 验证结果字典
    """
    print("\n" + "=" * 70)
    print("📊 JSONL 格式验证报告")
    print("=" * 70)

    print(f"1. ✅ JSONL 文件是否存在：{'是' if results['file_exists'] else '否'}")
    print(f"2. 📝 总行数：{results['total_lines']}")
    print(f"3. ✓ 有效 JSON 行数：{results['valid_json_lines']}")
    print(f"4. 🎯 Bbox 是否全在 [0, 1] 范围：{'是' if results['bbox_in_range'] else '否'}")
    if results['bbox_errors']:
        print(f"   ⚠️  Bbox 错误数量：{len(results['bbox_errors'])}")

    print(f"5. ✓ Status 字段是否有效：{'是' if results['status_valid'] else '否'}")
    if results['status_errors']:
        print(f"   ⚠️  Status 错误数量：{len(results['status_errors'])}")

    print(f"6. 🆔 ID 字段格式是否正确：{'是' if results['id_format_valid'] else '否'}")
    if results['id_errors']:
        print(f"   ⚠️  ID 错误数量：{len(results['id_errors'])}")

    print("=" * 70)

    # 显示样本数据
    if results['sample_data']:
        print("\n📋 样本数据（最后几行）：")
        print("-" * 70)
        for i, data in enumerate(results['sample_data'][:3], 1):
            print(f"\n样本 {i}:")
            print(f"  ID: {data.get('id', 'N/A')}")
            print(f"  Status: {data.get('status', 'N/A')}")
            print(f"  Class: {data.get('class_name', 'N/A')}")
            print(f"  Operation: {data.get('operation', 'N/A')}")
            if data.get('bbox'):
                print(f"  Bbox: {[f'{x:.3f}' for x in data['bbox']]}")

    print("=" * 70)

# ==================== 主程序 ====================

def main():
    """主程序入口"""
    logger.info("=" * 70)
    logger.info("🧪 单文件端到端测试")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # 1. 准备目录
        ensure_directories()

        # 2. 检查测试文件是否存在
        if not TEST_FILE.exists():
            logger.error(f"✗ 测试文件不存在：{TEST_FILE}")
            return

        logger.info(f"🎯 测试文件：{TEST_FILE}")

        # 3. 劫持文件
        logger.info("\n🔧 开始劫持文件...")
        hacked_file, scene_classes = hijack_scene_file(TEST_FILE, TEMP_RUN_DIR)

        if not hacked_file or not scene_classes:
            logger.error("✗ 劫持失败，程序退出")
            return

        # 4. 渲染每个场景
        logger.info(f"\n▶️ 开始渲染 {len(scene_classes)} 个场景...")
        rendered_count = 0
        failed_count = 0

        for scene_class in scene_classes:
            if render_hacked_scene(hacked_file, scene_class):
                rendered_count += 1
            else:
                failed_count += 1

        logger.info(f"\n📊 渲染完成：成功 {rendered_count}，失败 {failed_count}")

        # 5. 验证 JSONL 输出
        logger.info("\n🔍 验证 JSONL 输出格式...")
        time.sleep(2)  # 等待文件写入完成

        validation_results = validate_jsonl_output()
        print_validation_report(validation_results)

        # 6. 生成最终报告
        logger.info("\n" + "=" * 70)
        logger.info("✅ 测试完成")
        logger.info("=" * 70)
        logger.info(f"📁 劫持文件：{hacked_file}")
        logger.info(f"📁 输出文件：{OUTPUT_FILE}")
        logger.info(f"📄 日志文件：{LOG_FILE}")
        logger.info(f"⏱  总耗时：{time.time() - start_time:.2f} 秒")

        # 7. 生成问答报告
        print("\n📋 四个自检问题的答案：")
        print("-" * 70)

        q1_answer = "✅ 是" if validation_results['file_exists'] and validation_results['valid_json_lines'] > 0 else "❌ 否"
        q2_answer = "✅ 是" if validation_results['bbox_in_range'] else "❌ 否"
        q3_answer = "✅ 是" if validation_results['status_valid'] else "❌ 否"
        q4_answer = "✅ 是" if validation_results['id_format_valid'] else "❌ 否"

        print(f"1️⃣  是否成功生成了 JSONL？{q1_answer}")
        print(f"2️⃣  数据中的 bbox 是否全都在 [0, 1] 范围内？{q2_answer}")
        print(f"3️⃣  是否成功计算出了 status (\"keep\" / \"new\")？{q3_answer}")
        print(f"4️⃣  id 字段是否以类名加内存地址的形式呈现？{q4_answer}")

        print("=" * 70)

        # 检查是否通过所有测试
        all_passed = (
            validation_results['file_exists'] and
            validation_results['valid_json_lines'] > 0 and
            validation_results['bbox_in_range'] and
            validation_results['status_valid'] and
            validation_results['id_format_valid']
        )

        if all_passed:
            print("\n🎉 恭喜！所有测试通过，可以开始全量批处理！")
        else:
            print("\n⚠️  部分测试未通过，需要进一步调试。")

    except Exception as e:
        logger.error(f"❌ 程序执行失败：{e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
