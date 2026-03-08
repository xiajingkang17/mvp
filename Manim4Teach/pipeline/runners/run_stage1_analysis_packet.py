from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[3]
    repo_text = str(REPO_ROOT)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)

from Manim4Teach.pipeline.core.env import load_dotenv  # noqa: E402
from Manim4Teach.pipeline.core.question_parser import parse_requirement_inputs  # noqa: E402
from Manim4Teach.pipeline.stage1.client import build_stage1_client  # noqa: E402
from Manim4Teach.pipeline.stage1.stage1_analysis_packet import stage_analysis_packet  # noqa: E402


def _slugify(text: str, *, max_len: int = 36) -> str:
    raw = re.sub(r"\s+", "_", str(text or "").strip())
    raw = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]+", "", raw)
    raw = raw.strip("_")
    return (raw[:max_len] or "run").strip("_")


def _read_requirement(*, requirement: str, requirement_file: str) -> tuple[str, list[Path]]:
    return parse_requirement_inputs(requirement=requirement, requirement_file=requirement_file)


def _default_out_dir(requirement: str) -> Path:
    run_root = Path(__file__).resolve().parents[2] / "runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(requirement)
    return run_root / f"{ts}_{slug}" / "llm1"


def _load_env_file() -> Path:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"缺少 .env 文件: {env_path}")
    loaded = load_dotenv(path=env_path)
    if not loaded:
        raise RuntimeError(f".env 加载失败: {env_path}")
    return env_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manim4Teach LLM1: analysis_packet 生成")
    parser.add_argument("--requirement", type=str, default="")
    parser.add_argument("--requirement-file", type=str, default="")
    parser.add_argument(
        "--provider",
        choices=["claude", "anthropic"],
        default="claude",
        help="一级 LLM provider，claude 会映射为 anthropic",
    )
    parser.add_argument("--out-dir", type=str, default="", help="输出目录（默认自动创建）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = "anthropic" if args.provider == "claude" else args.provider
    env_path = _load_env_file()

    requirement, image_paths = _read_requirement(
        requirement=args.requirement,
        requirement_file=args.requirement_file,
    )
    out_dir = Path(args.out_dir) if args.out_dir else _default_out_dir(requirement)

    client = build_stage1_client(provider=provider)
    packet = stage_analysis_packet(client, requirement=requirement, image_paths=image_paths, out_dir=out_dir)

    print(f"[Manim4Teach][LLM1] provider: {provider}")
    print(f"[Manim4Teach][LLM1] env: {env_path}")
    print(f"[Manim4Teach][LLM1] mode: {packet.get('mode')}")
    print(f"[Manim4Teach][LLM1] images: {len(image_paths)}")
    print(f"[Manim4Teach][LLM1] output: {out_dir / 'stage1_analysis_packet.json'}")
    print(f"[Manim4Teach][LLM1] raw: {out_dir / 'stage1_analysis_packet_raw.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
