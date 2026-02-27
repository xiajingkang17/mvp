from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LLM_CONSTRAINTS = ROOT / "llm_constraints"
SCHEMA_FILE = ROOT / "schema" / "composite_graph_models.py"
SOLVER_CORE = ROOT / "render" / "composite" / "solver" / "core.py"


def _load_whitelist_types() -> set[str]:
    data = json.loads((LLM_CONSTRAINTS / "specs" / "constraints_whitelist.json").read_text(encoding="utf-8"))
    constraints = data.get("constraints", {})
    if not isinstance(constraints, dict):
        return set()
    return set(constraints.keys())


def _extract_literal_items_from_class(*, text: str, class_name: str) -> set[str]:
    class_match = re.search(rf"class\s+{class_name}\(BaseModel\):([\s\S]*?)(?:\nclass\s+\w+\(BaseModel\):|\Z)", text)
    if not class_match:
        return set()
    block = class_match.group(1)
    m = re.search(r'type:\s*Literal\[(.*?)\]', block, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def _load_schema_constraint_types() -> set[str]:
    text = SCHEMA_FILE.read_text(encoding="utf-8")
    return _extract_literal_items_from_class(text=text, class_name="GraphConstraint")


def _load_solver_types() -> set[str]:
    text = SOLVER_CORE.read_text(encoding="utf-8")
    items = re.findall(r'if ctype == "([^"]+)"', text)
    return set(items)


def main() -> int:
    whitelist = _load_whitelist_types()
    schema_types = _load_schema_constraint_types()
    solver_types = _load_solver_types()

    ok = True

    missing_in_schema = sorted(whitelist - schema_types)
    missing_in_solver = sorted(whitelist - solver_types)
    unknown_in_whitelist = sorted((schema_types | solver_types) - whitelist)

    if missing_in_schema:
        ok = False
        print("Missing in schema Literal:", ", ".join(missing_in_schema))
    if missing_in_solver:
        ok = False
        print("Missing in solver dispatch:", ", ".join(missing_in_solver))
    if unknown_in_whitelist:
        ok = False
        print("Present in schema/solver constraints but absent in whitelist:", ", ".join(unknown_in_whitelist))

    if ok:
        print("OK: constraints whitelist/schema/solver are consistent.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
