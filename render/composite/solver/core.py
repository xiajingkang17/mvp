from __future__ import annotations

from dataclasses import dataclass

from schema.composite_graph_models import CompositeGraph, GraphConstraint

from render.composite.types import ConstraintResidual, PartGeometry, Pose, SolveResult, rotate_vec

from .attach import apply as apply_attach, measure as measure_attach
from .distance import apply as apply_distance, measure as measure_distance
from .midpoint import apply as apply_midpoint, measure as measure_midpoint
from .on_track_pose import apply as apply_on_track_pose, measure as measure_on_track_pose


@dataclass(frozen=True)
class SolveOptions:
    max_iters: int = 80
    tolerance: float = 1e-3


@dataclass(frozen=True)
class _RigidMemberTemplate:
    leader: str
    local_x: float
    local_y: float
    theta_offset: float
    scale_ratio: float


@dataclass(frozen=True)
class _RigidState:
    members_by_leader: dict[str, list[str]]
    template_by_part: dict[str, _RigidMemberTemplate]

    def _rebase_group_from_driver(self, *, part_id: str, poses: dict[str, Pose]) -> None:
        driver_template = self.template_by_part.get(part_id)
        if driver_template is None:
            return
        leader = driver_template.leader
        if leader not in poses:
            return

        driver_pose = poses.get(part_id)
        if driver_pose is None:
            return
        leader_pose = poses[leader]

        if abs(driver_template.scale_ratio) <= 1e-9:
            leader_scale = float(leader_pose.scale)
        else:
            leader_scale = float(driver_pose.scale) / float(driver_template.scale_ratio)
        leader_theta = float(driver_pose.theta) - float(driver_template.theta_offset)
        rel_x, rel_y = rotate_vec(
            float(driver_template.local_x) * float(leader_scale),
            float(driver_template.local_y) * float(leader_scale),
            float(leader_theta),
        )
        leader_x = float(driver_pose.x) - rel_x
        leader_y = float(driver_pose.y) - rel_y

        leader_pose.x = leader_x
        leader_pose.y = leader_y
        leader_pose.theta = leader_theta
        leader_pose.scale = leader_scale

        for member_id in self.members_by_leader.get(leader, []):
            member_pose = poses.get(member_id)
            member_template = self.template_by_part.get(member_id)
            if member_pose is None or member_template is None:
                continue
            offset_x, offset_y = rotate_vec(
                float(member_template.local_x) * float(leader_scale),
                float(member_template.local_y) * float(leader_scale),
                float(leader_theta),
            )
            member_pose.x = leader_x + offset_x
            member_pose.y = leader_y + offset_y
            member_pose.theta = float(leader_theta) + float(member_template.theta_offset)
            member_pose.scale = float(leader_scale) * float(member_template.scale_ratio)

    def stabilize_from_parts(self, *, part_ids: list[str], poses: dict[str, Pose]) -> None:
        seen_leaders: set[str] = set()
        for part_id in part_ids:
            template = self.template_by_part.get(part_id)
            if template is None:
                continue
            if template.leader in seen_leaders:
                continue
            self._rebase_group_from_driver(part_id=part_id, poses=poses)
            seen_leaders.add(template.leader)


def _first_nonempty_str(args: dict, *keys: str) -> str | None:
    for key in keys:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"1", "true", "yes", "on"}
    return False


def _normalize_angle(angle: float) -> float:
    value = float(angle) % 360.0
    if value > 180.0:
        value -= 360.0
    return value


def _pose_changed(before: Pose, after: Pose, *, eps: float = 1e-9) -> bool:
    return (
        abs(float(before.x) - float(after.x)) > eps
        or abs(float(before.y) - float(after.y)) > eps
        or abs(_normalize_angle(float(before.theta) - float(after.theta))) > eps
        or abs(float(before.scale) - float(after.scale)) > eps
    )


def _constraint_part_refs(args: dict) -> list[str]:
    keys = (
        "part_id",
        "part_a",
        "part_b",
        "from_part_id",
        "to_part_id",
        "source_part_id",
        "target_part_id",
        "part_1",
        "part_2",
    )
    refs: list[str] = []
    seen: set[str] = set()
    for key in keys:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            part_id = value.strip()
            if part_id not in seen:
                refs.append(part_id)
                seen.add(part_id)
    return refs


class _UnionFind:
    def __init__(self, nodes: list[str]) -> None:
        self.parent = {node: node for node in nodes}

    def find(self, node: str) -> str:
        root = self.parent.get(node, node)
        while root != self.parent.get(root, root):
            root = self.parent[root]
        cur = node
        while cur in self.parent and self.parent[cur] != root:
            nxt = self.parent[cur]
            self.parent[cur] = root
            cur = nxt
        self.parent.setdefault(node, root)
        return root

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _prepare_rigid_state(
    *,
    constraints: list[GraphConstraint],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    options: SolveOptions,
) -> tuple[list[GraphConstraint], _RigidState | None]:
    rigid_constraints: list[GraphConstraint] = []
    rigid_ids: set[str] = set()
    rigid_edges: list[tuple[str, str]] = []
    for constraint in constraints:
        if constraint.type != "attach":
            continue
        args = dict(constraint.args or {})
        if not _as_bool(args.get("rigid")):
            continue
        part_a = _first_nonempty_str(args, "part_a", "from_part_id", "source_part_id", "part_id")
        part_b = _first_nonempty_str(args, "part_b", "to_part_id", "target_part_id")
        if not part_a or not part_b:
            continue
        if part_a not in poses or part_b not in poses or part_a not in geoms or part_b not in geoms:
            continue
        rigid_constraints.append(constraint)
        rigid_ids.add(constraint.id)
        rigid_edges.append((part_a, part_b))

    if not rigid_constraints:
        return list(constraints), None

    for _ in range(max(1, options.max_iters)):
        max_residual = 0.0
        for constraint in rigid_constraints:
            residual = apply_attach(args=dict(constraint.args or {}), poses=poses, geoms=geoms)
            if residual > max_residual:
                max_residual = residual
        if max_residual <= options.tolerance:
            break

    nodes = sorted({item for edge in rigid_edges for item in edge})
    uf = _UnionFind(nodes)
    for a, b in rigid_edges:
        uf.union(a, b)

    members_by_root: dict[str, list[str]] = {}
    for node in nodes:
        root = uf.find(node)
        members_by_root.setdefault(root, []).append(node)

    members_by_leader: dict[str, list[str]] = {}
    template_by_part: dict[str, _RigidMemberTemplate] = {}

    for members in members_by_root.values():
        ordered = sorted(members)
        leader = ordered[0]
        leader_pose = poses[leader]
        leader_scale = float(leader_pose.scale)
        if abs(leader_scale) <= 1e-9:
            leader_scale = 1.0
        leader_theta = float(leader_pose.theta)
        leader_x = float(leader_pose.x)
        leader_y = float(leader_pose.y)
        members_by_leader[leader] = ordered

        for part_id in ordered:
            pose = poses[part_id]
            dx = float(pose.x) - leader_x
            dy = float(pose.y) - leader_y
            rx, ry = rotate_vec(dx, dy, -leader_theta)
            local_x = float(rx) / float(leader_scale)
            local_y = float(ry) / float(leader_scale)
            scale_ratio = float(pose.scale) / float(leader_scale)
            theta_offset = _normalize_angle(float(pose.theta) - leader_theta)
            template_by_part[part_id] = _RigidMemberTemplate(
                leader=leader,
                local_x=local_x,
                local_y=local_y,
                theta_offset=theta_offset,
                scale_ratio=scale_ratio,
            )

    active_constraints = [constraint for constraint in constraints if constraint.id not in rigid_ids]
    return active_constraints, _RigidState(members_by_leader=members_by_leader, template_by_part=template_by_part)


def _apply_constraint(
    *,
    constraint: GraphConstraint,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict]],
) -> float:
    args = dict(constraint.args or {})
    ctype = constraint.type

    if ctype == "attach":
        return apply_attach(args=args, poses=poses, geoms=geoms)
    if ctype == "on_track_pose":
        return apply_on_track_pose(args=args, poses=poses, geoms=geoms, tracks=tracks)
    if ctype == "midpoint":
        return apply_midpoint(args=args, poses=poses, geoms=geoms)
    if ctype == "distance":
        return apply_distance(args=args, poses=poses, geoms=geoms)
    raise ValueError(f"Unsupported constraint type: {ctype}")


def _measure_residual(
    *,
    constraint: GraphConstraint,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict]],
    tolerance: float,
) -> ConstraintResidual:
    args = dict(constraint.args or {})
    ctype = constraint.type

    if ctype == "attach":
        residual = measure_attach(args=args, poses=poses, geoms=geoms)
    elif ctype == "on_track_pose":
        residual = measure_on_track_pose(args=args, poses=poses, geoms=geoms, tracks=tracks)
    elif ctype == "midpoint":
        residual = measure_midpoint(args=args, poses=poses, geoms=geoms)
    elif ctype == "distance":
        residual = measure_distance(args=args, poses=poses, geoms=geoms)
    else:
        raise ValueError(f"Unsupported constraint type: {ctype}")

    return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")


def solve_static(
    graph: CompositeGraph,
    *,
    geometries: dict[str, PartGeometry],
    options: SolveOptions | None = None,
) -> SolveResult:
    opts = options or SolveOptions()
    poses = {
        part.id: Pose(
            x=float(part.seed_pose.x),
            y=float(part.seed_pose.y),
            theta=float(part.seed_pose.theta),
            scale=float(part.seed_pose.scale),
            z=float(part.seed_pose.z),
        )
        for part in graph.parts
    }
    tracks = {track.id: (track.type, dict(track.data or {})) for track in graph.tracks}

    active_constraints, rigid_state = _prepare_rigid_state(
        constraints=list(graph.constraints),
        poses=poses,
        geoms=geometries,
        options=opts,
    )

    converged = False
    for _ in range(max(1, opts.max_iters)):
        max_residual = 0.0
        for constraint in active_constraints:
            args = dict(constraint.args or {})
            involved = _constraint_part_refs(args) if rigid_state is not None else []
            before = {part_id: poses[part_id].copy() for part_id in involved if part_id in poses}
            residual = _apply_constraint(constraint=constraint, poses=poses, geoms=geometries, tracks=tracks)
            if rigid_state is not None and before:
                changed_parts = [part_id for part_id, prev_pose in before.items() if _pose_changed(prev_pose, poses[part_id])]
                if changed_parts:
                    rigid_state.stabilize_from_parts(part_ids=changed_parts, poses=poses)
            if residual > max_residual:
                max_residual = residual
        if max_residual <= opts.tolerance:
            converged = True
            break

    residuals = [
        _measure_residual(
            constraint=constraint,
            poses=poses,
            geoms=geometries,
            tracks=tracks,
            tolerance=opts.tolerance,
        )
        for constraint in graph.constraints
    ]
    if not converged:
        converged = all(item.satisfied for item in residuals if item.hard)
    return SolveResult(poses=poses, residuals=residuals, converged=converged)
