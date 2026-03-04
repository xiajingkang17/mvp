from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunLayout:
    """
    运行产物目录布局（统一约定，便于 case 回归与分阶段调试）：

    <run_dir>/
      - requirement.txt
      - scene.py              # 导出（便于直接运行），内容来自 llm4/scene.py
      - final.mp4             # 导出（便于直接取用），内容来自 render/final.mp4
      - llm1/ ... llm5/
      - render/
    """

    run_dir: Path
    llm4_dir_name: str = "llm4"

    @classmethod
    def from_run_dir(cls, run_dir: Path, *, llm4_dir_name: str = "llm4") -> "RunLayout":
        return cls(run_dir=run_dir, llm4_dir_name=llm4_dir_name)

    # -------- dirs --------
    @property
    def llm1_dir(self) -> Path:
        return self.run_dir / "llm1"

    @property
    def llm2_dir(self) -> Path:
        return self.run_dir / "llm2"

    @property
    def llm3_dir(self) -> Path:
        return self.run_dir / "llm3"

    @property
    def llm35_dir(self) -> Path:
        return self.run_dir / "llm35"

    @property
    def llm4_dir(self) -> Path:
        return self.run_dir / self.llm4_dir_name

    @property
    def llm5_dir(self) -> Path:
        return self.run_dir / "llm5"

    @property
    def render_dir(self) -> Path:
        return self.run_dir / "render"

    @property
    def render_media_dir(self) -> Path:
        return self.render_dir / "media"

    # -------- exports (root conveniences) --------
    @property
    def requirement_txt(self) -> Path:
        return self.run_dir / "requirement.txt"

    @property
    def exported_scene_py(self) -> Path:
        return self.run_dir / "scene.py"

    @property
    def exported_final_mp4(self) -> Path:
        return self.run_dir / "final.mp4"

    # -------- llm1 --------
    @property
    def llm1_system_prompt(self) -> Path:
        return self.llm1_dir / "system_prompt.md"

    @property
    def stage1_analysis_json(self) -> Path:
        return self.llm1_dir / "stage1_analysis.json"

    @property
    def stage1_problem_solving_json(self) -> Path:
        return self.llm1_dir / "stage1_problem_solving.json"

    @property
    def stage1_drawing_brief_json(self) -> Path:
        return self.llm1_dir / "stage1_drawing_brief.json"

    @property
    def stage1_json(self) -> Path:
        return self.llm1_dir / "stage1_analyst.json"

    @property
    def stage1_raw(self) -> Path:
        return self.llm1_dir / "stage1_analyst_raw.txt"

    # -------- llm2 --------
    @property
    def llm2_system_prompt(self) -> Path:
        return self.llm2_dir / "system_prompt.md"

    @property
    def stage2_json(self) -> Path:
        return self.llm2_dir / "stage2_scene_plan.json"

    @property
    def stage2_raw(self) -> Path:
        return self.llm2_dir / "stage2_scene_plan_raw.txt"

    # -------- llm3 --------
    @property
    def llm3_system_prompt(self) -> Path:
        return self.llm3_dir / "system_prompt.md"

    @property
    def stage3_json(self) -> Path:
        return self.llm3_dir / "stage3_scene_designs.json"

    @property
    def stage3_raw_batch(self) -> Path:
        return self.llm3_dir / "stage3_scene_designs_raw.txt"

    def stage3_raw_scene(self, scene_id: str) -> Path:
        sid = scene_id.strip() or "scene_unknown"
        return self.llm3_dir / f"stage3_{sid}_raw.txt"

    def stage3_scene_dir(self, scene_id: str) -> Path:
        sid = scene_id.strip() or "scene_unknown"
        return self.llm3_dir / "scenes" / sid

    def stage3_scene_json(self, scene_id: str) -> Path:
        return self.stage3_scene_dir(scene_id) / "design.json"

    # -------- llm3.5 --------
    @property
    def llm35_system_prompt(self) -> Path:
        return self.llm35_dir / "system_prompt.md"

    @property
    def stage35_json(self) -> Path:
        return self.llm35_dir / "stage35_scene_layouts.json"

    @property
    def stage35_raw_batch(self) -> Path:
        return self.llm35_dir / "stage35_scene_layouts_raw.txt"

    def stage35_raw_scene(self, scene_id: str) -> Path:
        sid = scene_id.strip() or "scene_unknown"
        return self.llm35_dir / f"stage35_{sid}_raw.txt"

    def stage35_scene_dir(self, scene_id: str) -> Path:
        sid = scene_id.strip() or "scene_unknown"
        return self.llm35_dir / "scenes" / sid

    def stage35_scene_json(self, scene_id: str) -> Path:
        return self.stage35_scene_dir(scene_id) / "layout.json"

    # -------- llm4 --------
    @property
    def llm4_system_prompt(self) -> Path:
        return self.llm4_dir / "system_prompt.md"

    @property
    def stage4_raw(self) -> Path:
        return self.llm4_dir / "stage4_codegen_raw.txt"

    @property
    def stage4_meta(self) -> Path:
        return self.llm4_dir / "stage4_codegen_meta.json"

    @property
    def llm4_scene_py(self) -> Path:
        return self.llm4_dir / "scene.py"

    # -------- llm5 --------
    @property
    def llm5_system_prompt(self) -> Path:
        return self.llm5_dir / "system_prompt.md"

    def llm5_fix_raw(self, attempt: int) -> Path:
        n = max(1, int(attempt))
        return self.llm5_dir / f"fix_raw_{n}.txt"

    # -------- render --------
    def render_stdout(self, attempt: int) -> Path:
        return self.render_dir / f"render_stdout_{attempt}.txt"

    def render_stderr(self, attempt: int) -> Path:
        return self.render_dir / f"render_stderr_{attempt}.txt"

    @property
    def render_final_mp4(self) -> Path:
        return self.render_dir / "final.mp4"
