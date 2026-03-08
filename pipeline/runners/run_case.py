from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run_cmd(args: list[str]) -> int:
    proc = subprocess.run(args, text=True)
    return int(proc.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manim4Teach case runner (question.txt -> LLM1 -> LLM2)")
    parser.add_argument(
        "--case-dir",
        type=str,
        default="Manim4Teach/cases/case_001",
        help="case 目录，必须包含 question.txt",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "anthropic"],
        default="claude",
        help="LLM provider（LLM1/LLM2 同步）",
    )
    parser.add_argument("--max-rounds", type=int, default=3, help="LLM2 修稿轮数，建议 2-4")
    parser.add_argument("--skip-preview", action="store_true", help="跳过 LLM2 低清预览")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).resolve()
    question_file = case_dir / "question.txt"
    if not question_file.exists():
        raise FileNotFoundError(f"未找到 question.txt: {question_file}")

    llm1_out = case_dir / "llm1"
    llm2_out = case_dir / "llm2"

    repo_root = Path(__file__).resolve().parents[3]
    stage1_runner = repo_root / "Manim4Teach" / "pipeline" / "runners" / "run_stage1_analysis_packet.py"
    stage2_runner = repo_root / "Manim4Teach" / "pipeline" / "runners" / "run_llm2_loop.py"

    print(f"[Case] case_dir: {case_dir}")
    print(f"[Case] question: {question_file}")
    print("[Case] Step 1/2: run LLM1 analysis_packet")
    cmd_stage1 = [
        sys.executable,
        str(stage1_runner),
        "--requirement-file",
        str(question_file),
        "--provider",
        args.provider,
        "--out-dir",
        str(llm1_out),
    ]
    rc = _run_cmd(cmd_stage1)
    if rc != 0:
        print(f"[Case] LLM1 failed with exit code {rc}")
        return rc

    analysis_packet_path = llm1_out / "stage1_analysis_packet.json"
    if not analysis_packet_path.exists():
        raise FileNotFoundError(f"LLM1 未产出 analysis_packet: {analysis_packet_path}")

    print("[Case] Step 2/2: run LLM2 director loop")
    cmd_stage2 = [
        sys.executable,
        str(stage2_runner),
        "--analysis-packet",
        str(analysis_packet_path),
        "--requirement-file",
        str(question_file),
        "--provider",
        args.provider,
        "--max-rounds",
        str(max(1, int(args.max_rounds))),
        "--out-dir",
        str(llm2_out),
    ]
    if args.skip_preview:
        cmd_stage2.append("--skip-preview")
    rc = _run_cmd(cmd_stage2)
    if rc != 0:
        print(f"[Case] LLM2 failed with exit code {rc}")
        return rc

    print("[Case] done")
    print(f"[Case] LLM1 output: {analysis_packet_path}")
    print(f"[Case] LLM2 final scene: {llm2_out / 'final' / 'scene.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
