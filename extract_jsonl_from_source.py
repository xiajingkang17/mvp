#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3b1b 视频源码劫持与自动化数据提取脚本

功能：
1. 递归扫描视频源码目录，定位包含 Scene 类的 Python 文件
2. 劫持这些文件，将所有 Scene 子类替换为 DataGenScene
3. 在后台静默渲染这些劫持后的场景，触发数据抓取
4. 自动化处理 355 个核心动画文件
"""

import re
import subprocess
import sys
import logging
import os
from pathlib import Path
from typing import List, Set, Tuple
import traceback
import hashlib
import time

# ==================== 全局配置 ====================

# 源码根目录（所有 3b1b 视频源码的存放位置）
SOURCE_DIR = Path("/Users/chenshutong/Desktop/3b1b/videos-master")

# 临时修改后的代码存放目录（劫持后的代码将保存在这里）
TEMP_RUN_DIR = Path("/Users/chenshutong/Desktop/Temp_Hacked_Scenes")

# 数据输出目录（DataGenScene 生成的 JSONL 文件将保存在这里）
OUTPUT_DIR = Path("/Users/chenshutong/Desktop/Manim_Dataset_Output")

# ManimGL 渲染命令
MANIM_CMD = "manimgl"

# 渲染参数：-w 写文件（无头模式），-l 最低画质（480p, 15fps）
RENDER_FLAGS = ["-w", "-l"]

# 日志配置
LOG_FILE = Path("/Users/chenshutong/Desktop/3b1b/extraction_log.txt")

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
    logger.info(f"✓ 目录准备完成：\n  - 临时代码目录：{TEMP_RUN_DIR}\n  - 输出数据目录：{OUTPUT_DIR}")

def scan_scene_files(source_dir: Path) -> List[Path]:
    """递归扫描源码目录"""
    logger.info(f"🔍 开始扫描源码目录：{source_dir}")

    scene_files = []
    scanned_count = 0
    skipped_count = 0

    for py_file in source_dir.rglob("*.py"):
        scanned_count += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if SCENE_CLASS_PATTERN.search(content):
                scene_files.append(py_file)
                logger.debug(f"  ✓ 发现 Scene 文件：{py_file.relative_to(source_dir)}")
            else:
                skipped_count += 1
        except Exception as e:
            logger.warning(f"  ⚠ 读取文件失败 {py_file}：{e}")
            continue

    logger.info(f"📊 扫描完成：\n  - 扫描文件总数：{scanned_count}\n  - 包含 Scene 的文件：{len(scene_files)}\n  - 跳过的文件：{skipped_count}")
    return scene_files

def extract_scene_classes(content: str) -> List[str]:
    """提取场景类名"""
    matches = SCENE_CLASS_PATTERN.findall(content)
    class_names = [match[0] for match in matches]
    return class_names

def hijack_scene_file(source_file: Path, output_dir: Path) -> Tuple[Path, List[str]]:
    """劫持 Scene 文件（强化资产拦截版）"""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        scene_classes = extract_scene_classes(content)
        if not scene_classes:
            return None, []
        if HACKED_MARK_PATTERN.search(content):
            return None, []

        hacked_content = content

        # [核心修复 1] 强制抹除导致崩溃的 3b1b 废弃本地导包
        hacked_content = re.sub(r'^\s*from\s+manim_imports_ext\s+import\s+.*$', '', hacked_content, flags=re.MULTILINE)
        hacked_content = re.sub(r'^\s*import\s+manim_imports_ext.*$', '', hacked_content, flags=re.MULTILINE)

        # [核心修复 4 - 终极资产拦截] 强行抹除/伪造动画小人资产 (Pi Creature)
        # 将各类小人实例全部替换为空的 VGroup()，完美绕过 SVG 报错，且不影响后续动画逻辑
        hacked_content = re.sub(r'\bMortimer\s*\([^)]*\)', 'VGroup()', hacked_content)
        hacked_content = re.sub(r'\bRandolph\s*\([^)]*\)', 'VGroup()', hacked_content)
        hacked_content = re.sub(r'\bPiCreature\s*\([^)]*\)', 'VGroup()', hacked_content)
        hacked_content = re.sub(r'\bTeacher\s*\([^)]*\)', 'VGroup()', hacked_content)
        hacked_content = re.sub(r'\bStudent\s*\([^)]*\)', 'VGroup()', hacked_content)
        # 防止 VGroup() 执行 Blink(眨眼) 动画时崩溃，替换为 Wait
        hacked_content = re.sub(r'\bBlink\s*\([^)]*\)', 'Wait()', hacked_content)

        # [智能锚点注入] 提取并重组 __future__ 语句
        future_pattern = re.compile(r'^(from __future__ import .+)$', re.MULTILINE)
        future_matches = future_pattern.findall(hacked_content)

        # 从原代码中移除 __future__ 语句
        hacked_content = future_pattern.sub('', hacked_content)
        hacked_content = re.sub(r'^\n+', '', hacked_content, count=1)

        # [核心修复 2] 注入强语义组件
        hijack_imports = (
            '\n# HACKED_BY_DATA_GEN_SCRIPT\n'
            'from data_gen_base import DataGenScene\n'
            'from enhanced_square import Square\n'
            'from enhanced_tex import Tex, TexMobject\n'
            '\n# --- 3b1b 历史遗留常量补丁 ---\n'
            'DEFAULT_STROKE_WIDTH = 4\n'
        )

        # 安全拼接：Future 语句 -> 劫持导入 -> 代码本体
        future_str = '\n'.join(future_matches) + '\n' if future_matches else ''
        hacked_content = future_str + hijack_imports + '\n' + hacked_content

        # 替换 Scene 为 DataGenScene
        hacked_content = SCENE_CLASS_PATTERN.sub(r'class \1(DataGenScene):', hacked_content)

        relative_path = source_file.relative_to(SOURCE_DIR)
        output_file = output_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(hacked_content)

        return output_file, scene_classes
    except Exception as e:
        logger.error(f"  ✗ 劫持失败 {source_file}：{e}")
        return None, []

def render_hacked_scene(hacked_file: Path, scene_class: str) -> bool:
    """在后台静默渲染劫持后的场景"""
    try:
        cmd = [
            MANIM_CMD,
            str(hacked_file),
            scene_class,
            *RENDER_FLAGS
        ]

        logger.info(f"    ▶ 开始渲染：{scene_class}")

        hijacked_env = os.environ.copy()
        WASHED_DIR = Path("/Users/chenshutong/Desktop/3b1b/washed_manim_components").resolve()
        MAIN_DIR = Path("/Users/chenshutong/Desktop/3b1b").resolve()
        SOURCE_DIR = Path("/Users/chenshutong/Desktop/3b1b/videos-master").resolve()
        hijacked_env["PYTHONPATH"] = f"{WASHED_DIR}:{MAIN_DIR}:{SOURCE_DIR}:{hijacked_env.get('PYTHONPATH', '')}"

        result = subprocess.run(
            cmd,
            env=hijacked_env,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=hacked_file.parent
        )

        if result.returncode == 0:
            logger.info(f"    ✓ 渲染成功：{scene_class}")
            return True
        else:
            logger.error(f"    ⚠ 渲染失败：{scene_class}")
            logger.error(f"    ====== 真实报错信息开始 ======\n{result.stderr}\n    ====== 真实报错信息结束 ======")
            return False

    except subprocess.TimeoutExpired:
        logger.warning(f"    ⏱ 渲染超时：{scene_class}")
        return False
    except Exception as e:
        logger.error(f"    ✗ 渲染异常 {scene_class}：{e}")
        logger.debug(traceback.format_exc())
        return False

def process_single_file(source_file: Path) -> dict:
    """处理单个源文件：劫持并渲染"""
    result = {
        'source_file': str(source_file),
        'hacked_file': None,
        'scene_classes': [],
        'rendered': 0,
        'failed': 0,
        'success': False
    }

    try:
        hacked_file, scene_classes = hijack_scene_file(source_file, TEMP_RUN_DIR)

        if not hacked_file or not scene_classes:
            result['success'] = True
            return result

        result['hacked_file'] = str(hacked_file)
        result['scene_classes'] = scene_classes

        for scene_class in scene_classes:
            if render_hacked_scene(hacked_file, scene_class):
                result['rendered'] += 1
            else:
                result['failed'] += 1

        result['success'] = True

    except Exception as e:
        logger.error(f"✗ 处理文件异常 {source_file}：{e}")
        logger.debug(traceback.format_exc())

    return result

def generate_summary_report(results: List[dict]) -> str:
    """生成处理结果摘要报告"""
    total_files = len(results)
    success_files = sum(1 for r in results if r['success'])
    total_scenes = sum(len(r['scene_classes']) for r in results)
    rendered_scenes = sum(r['rendered'] for r in results)
    failed_scenes = sum(r['failed'] for r in results)

    report = f"""
╔═══════════════════════════════════════════════════════════╗
║           3b1b 视频源码劫持与数据提取完成报告             ║
╠═══════════════════════════════════════════════════════════╣
║  处理文件总数：{total_files:<40} ║
║  成功处理：   {success_files:<40} ║
╠═══════════════════════════════════════════════════════════╣
║  发现场景总数：{total_scenes:<40} ║
║  成功渲染：   {rendered_scenes:<40} ║
║  渲染失败：   {failed_scenes:<40} ║
╠═══════════════════════════════════════════════════════════╣
║  输出目录：                                         ║
║    - 劫持代码：{str(TEMP_RUN_DIR)[:40]:<30} ║
║    - 提取数据：{str(OUTPUT_DIR)[:40]:<30} ║
║    - 日志文件：{str(LOG_FILE)[:40]:<30} ║
╚═══════════════════════════════════════════════════════════╝
"""
    return report

# ==================== 主程序 ====================

def main():
    """主程序入口"""
    logger.info("=" * 70)
    logger.info("🚀 启动 3b1b 视频源码劫持与自动化数据提取程序 (单文件 PoC 2.0)")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        ensure_directories()

        target_file = SOURCE_DIR / "_2023" / "clt" / "main.py"
        scene_files = [target_file] if target_file.exists() else []

        if not scene_files:
            logger.warning(f"⚠ 未找到测试文件: {target_file}")
            return

        logger.info(f"🔧 开始处理靶标文件: {target_file.name}...")
        results = []

        for idx, source_file in enumerate(scene_files, 1):
            try:
                result = process_single_file(source_file)
                results.append(result)
            except Exception as e:
                logger.error(f"✗ 处理文件时发生异常：{e}")
                continue

        summary = generate_summary_report(results)
        logger.info("\n" + summary)

    except Exception as e:
        logger.error(f"❌ 程序执行失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()