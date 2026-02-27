from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LLM_CONSTRAINTS = ROOT / "llm_constraints"


def _load_constraint_types() -> set[str]:
    data = json.loads((LLM_CONSTRAINTS / "specs" / "constraints_whitelist.json").read_text(encoding="utf-8"))
    constraints = data.get("constraints", {})
    if not isinstance(constraints, dict):
        return set()
    return set(constraints.keys())


def _pattern_types() -> set[str]:
    result: set[str] = set()
    for path in (LLM_CONSTRAINTS / "patterns").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("constraints", []) or []:
            ctype = item.get("type")
            if isinstance(ctype, str) and ctype.strip():
                result.add(ctype.strip())
    return result


def _protocol_text() -> str:
    text_parts: list[str] = []
    for path in (LLM_CONSTRAINTS / "protocols").glob("*.md"):
        text_parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(text_parts).lower()


def main() -> int:
    types = _load_constraint_types()
    in_patterns = _pattern_types()
    protocol_text = _protocol_text()

    ok = True
    missing_pattern = sorted(types - in_patterns)
    if missing_pattern:
        ok = False
        print("Missing pattern examples for:", ", ".join(missing_pattern))

    missing_protocol = sorted([t for t in types if t.lower() not in protocol_text])
    if missing_protocol:
        ok = False
        print("Constraint names not mentioned in protocols:", ", ".join(missing_protocol))

    if ok:
        print("OK: whitelist constraints are covered by patterns and protocol docs.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

