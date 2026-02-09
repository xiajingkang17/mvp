from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.config import load_enums
from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion
from pipeline.prompting import load_prompt


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM2：生成 scene_draft.json")
    parser.add_argument("--case", default="cases/demo_001", help="case 目录，例如 cases/demo_001")
    parser.add_argument("--no-repair", action="store_true", help="解析失败时不做二次 JSON 修复请求")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    problem = (case_dir / "problem.md").read_text(encoding="utf-8")
    explanation = (case_dir / "explanation.txt").read_text(encoding="utf-8")
    out_path = case_dir / "scene_draft.json"

    enums = load_enums()
    allowed_object_types = sorted(enums["object_types"])
    prompt = load_prompt("llm2_scene_draft.md")

    user_payload = "\n".join(
        [
            "允许的 object.type：",
            json.dumps(allowed_object_types, ensure_ascii=False),
            "",
            "problem.md：",
            problem.strip(),
            "",
            "explanation.txt：",
            explanation.strip(),
            "",
            "请严格只输出一个 JSON 对象（输出必须以 `{` 开始、以 `}` 结束）。",
        ]
    )

    content = chat_completion([ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)])
    raw_path = case_dir / "llm2_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")

    try:
        data = load_json_from_llm(content)
    except Exception as e:  # noqa: BLE001
        if args.no_repair:
            print(f"LLM2 输出无法解析为 JSON：{e}。请查看：{raw_path}", file=sys.stderr)
            return 2

        repair_prompt = load_prompt("json_repair.md")
        repair_payload = "\n".join(
            [
                "目标：生成 scene_draft.json（根对象必须包含 scenes 数组）。",
                "允许的 object.type：",
                json.dumps(allowed_object_types, ensure_ascii=False),
                "",
                "problem.md：",
                problem.strip(),
                "",
                "explanation.txt：",
                explanation.strip(),
                "",
                "目标结构示例：",
                json.dumps(
                    {
                        "scenes": [
                            {
                                "id": "S1",
                                "intent": "一句话说明这一段讲什么",
                                "objects": [
                                    {
                                        "id": "o1",
                                        "type": "TextBlock",
                                        "params": {"text": "示例"},
                                        "style": {"size_level": "L"},
                                        "priority": 1,
                                    }
                                ],
                                "notes": "可选",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "",
                "原始输出如下（可能不是 JSON）：",
                content.strip(),
                "",
                "要求：只输出修复后的严格 JSON；如果原始输出不可用，请基于 problem.md 与 explanation.txt 重新生成。",
            ]
        )
        repaired = chat_completion(
            [ChatMessage(role="system", content=repair_prompt), ChatMessage(role="user", content=repair_payload)]
        )
        repair_raw_path = case_dir / "llm2_repair_raw.txt"
        repair_raw_path.write_text(repaired.strip() + "\n", encoding="utf-8")
        try:
            data = load_json_from_llm(repaired)
        except Exception as e2:  # noqa: BLE001
            print(
                f"LLM2 二次修复后仍无法解析为 JSON：{e2}。请查看：{raw_path} 与 {repair_raw_path}",
                file=sys.stderr,
            )
            return 2

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
