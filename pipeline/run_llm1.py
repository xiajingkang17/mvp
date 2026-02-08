from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.env import load_dotenv
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion
from pipeline.prompting import load_prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM1：生成 explanation.txt")
    parser.add_argument("--case", default="cases/demo_001", help="case 目录，例如 cases/demo_001")
    parser.add_argument("--problem", default=None, help="可选：指定题目文件路径（默认读取 case/problem.md）")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    explanation_path = case_dir / "explanation.txt"

    problem = problem_path.read_text(encoding="utf-8")
    prompt = load_prompt("llm1_explanation.md")

    content = chat_completion(
        [
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=f"题目如下：\n\n{problem}\n"),
        ]
    )

    explanation_path.write_text(content.strip() + "\n", encoding="utf-8")
    print(str(explanation_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
