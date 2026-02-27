from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AudienceLevel = Literal["beginner", "intermediate", "advanced"]
SceneFocus = Literal[
    "hook_question",
    "goal",
    "knowns",
    "diagram",
    "assumption",
    "principle",
    "core_equation",
    "derive_step",
    "substitute_compute",
    "intermediate_result",
    "conclusion",
    "check_sanity",
    "transition",
]


class NarrativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_concept: str = Field(min_length=1)
    narrative_goal: str = Field(min_length=1)
    audience_level: AudienceLevel


class NarrativeStyleGuide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str = Field(min_length=1)
    pacing: str = Field(min_length=1)
    color_intent: str | None = None
    transition_principles: list[str] = Field(default_factory=list)
    narration_rules: list[str] = Field(default_factory=list)


class NarrativeSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    concept_ref: str = Field(min_length=1)
    sub_question_id: str | None = None
    title: str = Field(min_length=1)
    narration: str = Field(min_length=1)
    visual_intent: str = Field(min_length=1)
    key_equations: list[str] = Field(default_factory=list)
    scene_focus: SceneFocus
    transition_hook: str | None = None
    duration_hint_s: int = Field(default=18, ge=3, le=120)


class NarrativePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis: NarrativeAnalysis
    global_arc: str = Field(min_length=1)
    ordered_concepts: list[str] = Field(default_factory=list, min_length=1)
    segments: list[NarrativeSegment] = Field(default_factory=list, min_length=1)
    style_guide: NarrativeStyleGuide
    explanation: str | None = None

    @model_validator(mode="after")
    def _validate_plan(self) -> "NarrativePlan":
        ordered_keys = [x.strip().lower() for x in self.ordered_concepts if x.strip()]
        if len(ordered_keys) != len(self.ordered_concepts):
            raise ValueError("ordered_concepts contains empty entries")
        if len(set(ordered_keys)) != len(ordered_keys):
            raise ValueError("ordered_concepts must not contain duplicates")

        if ordered_keys[-1] != self.analysis.target_concept.strip().lower():
            raise ValueError("analysis.target_concept must match ordered_concepts last item")

        segment_ids: set[str] = set()
        order_index = {name: idx for idx, name in enumerate(ordered_keys)}
        for seg in self.segments:
            seg_id = seg.id.strip()
            if seg_id in segment_ids:
                raise ValueError(f"duplicate segment id: {seg_id}")
            segment_ids.add(seg_id)

            concept_key = seg.concept_ref.strip().lower()
            if concept_key not in order_index:
                raise ValueError(f"segment concept_ref not in ordered_concepts: {seg.concept_ref}")

            for eq in seg.key_equations:
                if not str(eq).strip():
                    raise ValueError(f"segment key_equations contains empty equation: {seg.id}")

        last_segment_concept = self.segments[-1].concept_ref.strip().lower()
        if last_segment_concept != ordered_keys[-1]:
            raise ValueError("last segment must correspond to target concept")

        return self
