from __future__ import annotations

import argparse
import json
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
            "请严格只输出一个 JSON 对象。",
        ]
    )

    content = chat_completion([ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)])
    data = load_json_from_llm(content)

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
