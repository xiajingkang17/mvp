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
    parser = argparse.ArgumentParser(description="LLM3：生成 scene_layout.json")
    parser.add_argument("--case", default="cases/demo_001", help="case 目录，例如 cases/demo_001")
    parser.add_argument("--no-repair", action="store_true", help="解析失败时不做二次 JSON 修复请求")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    draft = json.loads((case_dir / "scene_draft.json").read_text(encoding="utf-8"))
    out_path = case_dir / "scene_layout.json"

    enums = load_enums()
    prompt = load_prompt("llm3_scene_layout.md")

    user_payload = "\n".join(
        [
            "允许的 layout.type：",
            json.dumps(sorted(enums["layout_types"]), ensure_ascii=False),
            "",
            "允许的 action.op：",
            json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
            "",
            "允许的 anim：",
            json.dumps(sorted(enums["anims"]), ensure_ascii=False),
            "",
            "scene_draft.json：",
            json.dumps(draft, ensure_ascii=False, indent=2),
            "",
            "请严格只输出一个 JSON 对象（输出必须以 `{` 开始、以 `}` 结束）。",
        ]
    )

    content = chat_completion([ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)])
    raw_path = case_dir / "llm3_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")

    try:
        data = load_json_from_llm(content)
    except Exception as e:  # noqa: BLE001
        if args.no_repair:
            print(f"LLM3 输出无法解析为 JSON：{e}。请查看：{raw_path}", file=sys.stderr)
            return 2

        repair_prompt = load_prompt("json_repair.md")
        repair_payload = "\n".join(
            [
                "目标：生成 scene_layout.json（根对象必须包含 scenes 数组）。",
                "允许的 layout.type：",
                json.dumps(sorted(enums["layout_types"]), ensure_ascii=False),
                "",
                "允许的 action.op：",
                json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
                "",
                "允许的 anim：",
                json.dumps(sorted(enums["anims"]), ensure_ascii=False),
                "",
                "scene_draft.json：",
                json.dumps(draft, ensure_ascii=False, indent=2),
                "",
                "目标结构示例：",
                json.dumps(
                    {
                        "scenes": [
                            {
                                "id": "S1",
                                "layout": {
                                    "type": "left_right",
                                    "slots": {"left": "o1", "right": "o2"},
                                    "params": {"left_ratio": 0.6},
                                },
                                "actions": [
                                    {"op": "play", "anim": "fade_in", "targets": ["o1"]},
                                    {"op": "wait", "duration": 0.4},
                                ],
                                "keep": ["o1"],
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
                "要求：只输出修复后的严格 JSON；如果原始输出不可用，请基于 scene_draft.json 重新生成。",
            ]
        )
        repaired = chat_completion(
            [ChatMessage(role="system", content=repair_prompt), ChatMessage(role="user", content=repair_payload)]
        )
        repair_raw_path = case_dir / "llm3_repair_raw.txt"
        repair_raw_path.write_text(repaired.strip() + "\n", encoding="utf-8")
        try:
            data = load_json_from_llm(repaired)
        except Exception as e2:  # noqa: BLE001
            print(
                f"LLM3 二次修复后仍无法解析为 JSON：{e2}。请查看：{raw_path} 与 {repair_raw_path}",
                file=sys.stderr,
            )
            return 2

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
