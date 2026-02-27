from __future__ import annotations

from schema.composite_graph_models import CompositeGraph

from ..types import PartGeometry, Pose
from .common import _arg
from .state_driver import evaluate_state_driver_target
from .track_motion import _apply_on_track, _apply_on_track_schedule


def apply_motions(
    graph: CompositeGraph,
    *,
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
    time_value: float = 0.0,
) -> dict[str, Pose]:
    updated = {part_id: pose.copy() for part_id, pose in poses.items()}
    tracks = {track.id: (track.type, dict(track.data or {})) for track in graph.tracks}
    for motion in graph.motions:
        if motion.type == "on_track":
            _apply_on_track(
                motion=motion,
                poses=updated,
                geometries=geometries,
                tracks=tracks,
                time_value=time_value,
            )
        elif motion.type == "on_track_schedule":
            _apply_on_track_schedule(
                motion=motion,
                poses=updated,
                geometries=geometries,
                tracks=tracks,
                time_value=time_value,
            )
        elif motion.type == "state_driver":
            target = evaluate_state_driver_target(
                motion,
                time_value=time_value,
                current_pose=updated.get(str(_arg(dict(motion.args or {}), "part_id", default=""))),
                handoff_state=None,
            )
            if target is None:
                continue
            part_id = str(target.get("part_id", "")).strip()
            if not part_id or part_id not in updated:
                continue
            pose = updated[part_id]
            pose.x = float(target["x"])
            pose.y = float(target["y"])
            pose.theta = float(target.get("theta", pose.theta))
    return updated


__all__ = ["apply_motions"]
