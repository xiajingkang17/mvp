from __future__ import annotations

from .common import (
    Any,
    LLMClient,
    Path,
    _split_analyst_payload,
    _write_text,
    assemble_analyst_payload,
)

def stage_analyst(client: LLMClient, *, requirement: str, out_dir: Path) -> dict[str, Any]:
    system = client.load_stage_system_prompt("analyst")
    user = requirement.strip()
    data, raw = client.generate_json(stage_key="analyst", system_prompt=system, user_prompt=user)
    _write_text(out_dir / "stage1_analyst_raw.txt", raw)
    analysis, problem_solving, drawing_brief = _split_analyst_payload(data)
    client.save_json(out_dir / "stage1_analysis.json", analysis)
    client.save_json(out_dir / "stage1_problem_solving.json", problem_solving)
    client.save_json(out_dir / "stage1_drawing_brief.json", drawing_brief)
    return assemble_analyst_payload(
        analysis=analysis,
        problem_solving=problem_solving,
        drawing_brief=drawing_brief,
    )


