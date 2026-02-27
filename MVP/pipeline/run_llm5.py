from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[1]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import write_text  # noqa: E402
from pipeline.rendering import detect_scene_classes  # noqa: E402
from pipeline.run_mvp import build_client, stage_fix_code  # noqa: E402
from pipeline.run_layout import RunLayout  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM5（fixer）：根据渲染报错修复单文件 scene.py")
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（包含 scene.py 与渲染日志）")
    p.add_argument("--py", type=str, default="llm4/scene.py", help="要修复的 Python 文件（默认 llm4/scene.py）")
    p.add_argument("--attempt", type=int, default=1, help="修复轮次（用于写 fix_raw_<attempt>.txt，默认 1）")
    p.add_argument("--stderr-file", type=str, default="", help="渲染错误日志文件路径")
    p.add_argument("--stderr", type=str, default="", help="直接传入 stderr 文本（和 --stderr-file 二选一）")
    p.add_argument("--class-name", type=str, default="", help="可选：显式指定目标 Scene 类名")
    return p.parse_args()


def _load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _resolve_stderr(args: argparse.Namespace, run_dir: Path) -> str:
    if args.stderr and args.stderr.strip():
        return args.stderr
    if args.stderr_file:
        return Path(args.stderr_file).read_text(encoding="utf-8")

    # 兜底：尝试读取最近一次 render_stderr_*.txt（新布局优先在 render/ 下）
    candidates = sorted(run_dir.glob("render/render_stderr_*.txt")) + sorted(run_dir.glob("render_stderr_*.txt"))
    if candidates:
        return candidates[-1].read_text(encoding="utf-8")

    raise SystemExit("缺少 stderr：请提供 --stderr-file 或 --stderr，或确保 run_dir 下存在 render_stderr_*.txt。")


def _resolve_class_name(args: argparse.Namespace, run_dir: Path, code: str) -> str:
    if args.class_name and args.class_name.strip():
        return args.class_name.strip()

    layout = RunLayout.from_run_dir(run_dir)
    meta = _load_json_if_exists(layout.stage4_meta)
    if not meta:
        # 兼容旧路径
        meta = _load_json_if_exists(run_dir / "stage4_codegen_meta.json")
    class_name = str(meta.get("class_name") or "").strip()
    if class_name:
        return class_name

    classes = detect_scene_classes(code)
    if classes:
        return classes[0]

    return "MainScene"


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")
    layout = RunLayout.from_run_dir(run_dir)

    py_path = (run_dir / args.py).resolve() if not Path(args.py).is_absolute() else Path(args.py)
    if not py_path.exists():
        raise SystemExit(f"缺少代码文件: {py_path}")

    code = py_path.read_text(encoding="utf-8")
    stderr = _resolve_stderr(args, run_dir)
    class_name = _resolve_class_name(args, run_dir, code)

    client = build_client()
    system = client.load_stage_system_prompt("fixer")
    write_text(layout.llm5_system_prompt, system.strip() + "\n")

    fixed = stage_fix_code(
        client,
        class_name=class_name,
        code=code,
        stderr=stderr,
        scene_dir=layout.llm5_dir,
        attempt=max(1, int(args.attempt)),
    )
    write_text(py_path, fixed)

    # 同步导出：llm4/scene.py <-> run_dir/scene.py
    try:
        if py_path.resolve() == layout.llm4_scene_py.resolve():
            write_text(layout.exported_scene_py, fixed)
        elif py_path.resolve() == layout.exported_scene_py.resolve():
            write_text(layout.llm4_scene_py, fixed)
    except Exception:  # noqa: BLE001
        pass

    # 更新 meta（如果修复后 class 变化了）
    classes = detect_scene_classes(fixed)
    new_class = classes[0] if classes else class_name
    meta_path = layout.stage4_meta
    meta = _load_json_if_exists(meta_path)
    meta.update(
        {
            "class_name": new_class,
            "last_fix_attempt": max(1, int(args.attempt)),
        }
    )
    write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")

    print(f"[LLM5] 已修复并写回: {py_path}（class_name={new_class}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
