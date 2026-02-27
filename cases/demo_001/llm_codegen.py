from __future__ import annotations

from typing import Any, Callable, Dict

from manim import *
import numpy as np

BuilderFn = Callable[[Dict[str, Any]], Mobject]
UpdaterFn = Callable[[Mobject, float, Dict[str, Any]], None]

# ==========================================
# Helper Functions
# ==========================================

def _get_color(palette: Dict[str, str], key: str, default: str = WHITE) -> ManimColor:
    return ManimColor(palette.get(key, default))

def _get_float(sizes: Dict[str, float], key: str, default: float = 1.0) -> float:
    return float(sizes.get(key, default))

def _get_parabola_points(x_dist: float, y_drop: float, num_points: int = 50) -> list[np.ndarray]:
    """Generates points for a parabola y = - (y_drop / x_dist^2) * x^2."""
    points = []
    for u in np.linspace(0, 1, num_points):
        x = u * x_dist
        y = -y_drop * (u**2)
        points.append(np.array([x, y, 0.0]))
    return points

# ==========================================
# Builders
# ==========================================

def builder_projectile_path(spec: Dict[str, Any]) -> Mobject:
    """
    Draws the parabolic trajectory from B to ground, plus decomposition arrows.
    """
    geom = dict(spec.get("geometry", {}) or {})
    style = dict(spec.get("style", {}) or {})
    layout = dict(geom.get("layout", {}))
    palette = dict(style.get("palette", {}))
    sizes = dict(style.get("sizes", {}))

    H = layout.get("height_H", 1.25)
    x_dist = layout.get("horizontal_distance_x", 2.0)

    # 1. Parabolic Curve (Dashed)
    curve_points = _get_parabola_points(x_dist, H)
    curve_vm = VMobject().set_points_as_corners(curve_points).make_smooth()
    dashed_curve = DashedVMobject(
        curve_vm,
        dashed_ratio=0.5,
        color=_get_color(palette, "curve_color"),
        stroke_width=_get_float(sizes, "stroke_width", 2.0)
    )

    # 2. Arrows (Decomposition)
    # Position arrows at roughly 30% of the path
    u_pos = 0.3
    pos_x = u_pos * x_dist
    pos_y = -H * (u_pos**2)
    pos_vec = np.array([pos_x, pos_y, 0.0])

    # Vertical Arrow (Gravity) - pointing down
    v_arrow_len = 0.8
    v_arrow = Arrow(
        start=pos_vec + np.array([0, v_arrow_len/2, 0]),
        end=pos_vec - np.array([0, v_arrow_len/2, 0]),
        color=_get_color(palette, "vertical_arrow_color"),
        buff=0,
        max_tip_length_to_length_ratio=0.3
    )
    
    # Horizontal Arrow (Inertia) - pointing right
    h_arrow_len = 0.8
    h_arrow = Arrow(
        start=pos_vec - np.array([h_arrow_len/2, 0, 0]),
        end=pos_vec + np.array([h_arrow_len/2, 0, 0]),
        color=_get_color(palette, "horizontal_arrow_color"),
        buff=0,
        max_tip_length_to_length_ratio=0.3
    )

    # Grouping
    group = VGroup(dashed_curve, v_arrow, h_arrow)
    
    # Store references for updater
    group.curve = dashed_curve
    group.v_arrow = v_arrow
    group.h_arrow = h_arrow
    
    return group

def builder_projectile_path_s5(spec: Dict[str, Any]) -> Mobject:
    """
    Static display of trajectory, arrows, and time label.
    """
    geom = dict(spec.get("geometry", {}) or {})
    style = dict(spec.get("style", {}) or {})
    palette = dict(style.get("palette", {}))
    sizes = dict(style.get("sizes", {}))
    meta = dict(spec.get("meta", {}))

    H = 1.25
    x_dist = 2.0

    # 1. Curve
    curve_points = _get_parabola_points(x_dist, H)
    curve_vm = VMobject().set_points_as_corners(curve_points).make_smooth()
    dashed_curve = DashedVMobject(
        curve_vm,
        dashed_ratio=0.5,
        color=_get_color(palette, "curve_color"),
        stroke_width=_get_float(sizes, "stroke_width", 2.0)
    )

    # 2. Arrows
    u_pos = 0.3
    pos_x = u_pos * x_dist
    pos_y = -H * (u_pos**2)
    pos_vec = np.array([pos_x, pos_y, 0.0])

    v_arrow = Arrow(
        start=pos_vec + np.array([0, 0.4, 0]),
        end=pos_vec - np.array([0, 0.4, 0]),
        color=_get_color(palette, "vertical_arrow_color"),
        buff=0
    )
    h_arrow = Arrow(
        start=pos_vec - np.array([0.4, 0, 0]),
        end=pos_vec + np.array([0.4, 0, 0]),
        color=_get_color(palette, "horizontal_arrow_color"),
        buff=0
    )

    # 3. Time Label
    # "t = 0.5s"
    latex_str = r"t = 0.5\text{s}"
    if meta.get("latex_items"):
        latex_str = meta["latex_items"][0]

    label = MathTex(
        latex_str,
        color=WHITE,
        font_size=_get_float(sizes, "font_size", 24)
    )
    label.next_to(v_arrow, LEFT, buff=0.1)

    group = VGroup(dashed_curve, v_arrow, h_arrow, label)
    return group

def builder_projectile_path_s6(spec: Dict[str, Any]) -> Mobject:
    """
    Shows ball at impact, ground distance arrow.
    """
    geom = dict(spec.get("geometry", {}) or {})
    style = dict(spec.get("style", {}) or {})
    layout = dict(geom.get("layout", {}))
    palette = dict(style.get("palette", {}))
    sizes = dict(style.get("sizes", {}))

    H = 1.25
    x_dist = layout.get("arrow_end_x", 2.0) - layout.get("arrow_start_x", 0.0)
    
    # 1. Static Parabola (Solid)
    curve_points = _get_parabola_points(x_dist, H)
    curve = VMobject().set_points_as_corners(curve_points).make_smooth()
    curve.set_color(_get_color(palette, "curve_color"))
    curve.set_stroke(width=_get_float(sizes, "stroke_width", 2.0))

    # 2. Ground Distance Arrow
    # Ground is at y = -H
    ground_y = -H
    start_x = 0.0
    end_x = x_dist
    
    # Double-headed arrow
    dist_arrow = Arrow(
        start=np.array([start_x, ground_y, 0]),
        end=np.array([end_x, ground_y, 0]),
        color=_get_color(palette, "distance_arrow_color"),
        buff=0.1,
        max_tip_length_to_length_ratio=0.2
    )
    
    # Label for x
    label = MathTex("x", color=_get_color(palette, "distance_arrow_color"))
    label.next_to(dist_arrow, DOWN, buff=0.1)

    group = VGroup(curve, dist_arrow, label)
    return group

def builder_final_path(spec: Dict[str, Any]) -> Mobject:
    """
    Assembles the full system: orbit, parabola, and ground.
    """
    geom = dict(spec.get("geometry", {}) or {})
    style = dict(spec.get("style", {}) or {})
    layout = dict(geom.get("layout", {}))
    palette = dict(style.get("palette", {}))
    sizes = dict(style.get("sizes", {}))

    h = layout.get("orbit_height_h", 0.8)
    H = layout.get("drop_height_H", 1.25)
    x_dist = layout.get("horizontal_distance_x", 2.0)

    # 1. Orbit (Arc)
    # Center of the circle is at (0, h) relative to B (0,0) if B is bottom.
    # Radius R = h.
    # A is at (-R, R) relative to center? No, A is at top.
    # Let's assume B is at (0,0). Center is (0, h).
    # A is at (-h, 2h) ? No, A is h above B.
    # If B is bottom, A is at angle 90 deg (pi/2) from vertical?
    # Let's assume a quarter circle from left to bottom.
    # Center at (0, h). Radius h.
    # B is at (0,0). A is at (-h, h).
    radius = h
    center = np.array([0, h, 0])
    
    # Create Arc from angle 90 (top) to 180 (left) to 270 (bottom)?
    # Standard Arc: angle 0 is right, 90 is up.
    # We want A (left) to B (bottom).
    # A is at 180 deg, B is at 270 deg.
    # Arc from 180 to 270.
    orbit = Arc(
        radius=radius,
        start_angle=PI,
        angle=-PI/2,
        color=_get_color(palette, "orbit_color"),
        stroke_width=_get_float(sizes, "stroke_width", 3.0),
        arc_center=center
    )

    # 2. Parabola
    curve_points = _get_parabola_points(x_dist, H)
    parabola = VMobject().set_points_as_corners(curve_points).make_smooth()
    parabola.set_color(_get_color(palette, "parabola_color"))
    parabola.set_stroke(width=_get_float(sizes, "stroke_width", 3.0))

    # 3. Ground System
    ground_y = -H
    ground_line = Line(
        start=np.array([-x_dist - 1, ground_y, 0]),
        end=np.array([x_dist + 1, ground_y, 0]),
        color=_get_color(palette, "ground_color"),
        stroke_width=2.0
    )
    
    # Ground Distance Arrow (reusing logic from S6)
    dist_arrow = Arrow(
        start=np.array([0.0, ground_y, 0]),
        end=np.array([x_dist, ground_y, 0]),
        color=_get_color(palette, "distance_arrow_color", "#AA00FF"),
        buff=0.1,
        max_tip_length_to_length_ratio=0.2
    )
    
    label_x = MathTex("x", color=_get_color(palette, "distance_arrow_color", "#AA00FF"))
    label_x.next_to(dist_arrow, DOWN, buff=0.1)

    # 4. Labels for A and B
    label_A = Text("A", font_size=24).move_to(np.array([-h, h, 0]) + LEFT*0.2)
    label_B = Text("B", font_size=24).move_to(np.array([0, 0, 0]) + DOWN*0.3)

    group = VGroup(orbit, parabola, ground_line, dist_arrow, label_x, label_A, label_B)
    return group

# ==========================================
# Updaters
# ==========================================

def updater_projectile_path(mobj: Mobject, t: float, spec: Dict[str, Any]) -> None:
    """
    Animates the drawing of the curve and fading in of arrows.
    """
    motion = dict(spec.get("motion", {}) or {})
    timing = dict(motion.get("timing", {}))
    
    draw_duration = _get_float(timing, "draw_duration_s", 1.5)
    arrow_fade_in = _get_float(timing, "arrow_fade_in_s", 0.5)
    
    # Total animation time
    total_time = draw_duration + arrow_fade_in
    
    # Normalize t to [0, 1] based on motion_span_s if needed, 
    # but here t is local time passed to updater.
    # We assume t goes from 0 to motion_span_s (2.0)
    
    # 1. Draw Curve
    if t < draw_duration:
        progress = t / draw_duration
        # Trim the curve
        # mobj.curve is the DashedVMobject
        # We can't easily trim a DashedVMobject dynamically without rebuilding.
        # Instead, we use pointwise definition or opacity.
        # For simplicity in this constraint, we fade in the curve.
        mobj.curve.set_opacity(min(progress * 1.5, 1.0))
    else:
        mobj.curve.set_opacity(1.0)

    # 2. Fade in Arrows
    if t > draw_duration:
        arrow_t = t - draw_duration
        progress = min(arrow_t / arrow_fade_in, 1.0)
        mobj.v_arrow.set_opacity(progress)
        mobj.h_arrow.set_opacity(progress)
    else:
        mobj.v_arrow.set_opacity(0.0)
        mobj.h_arrow.set_opacity(0.0)

# ==========================================
# Registry
# ==========================================

BUILDERS: dict[str, BuilderFn] = {
    "projectile_path": builder_projectile_path,
    "projectile_path_s5": builder_projectile_path_s5,
    "projectile_path_s6": builder_projectile_path_s6,
    "final_path": builder_final_path,
}

UPDATERS: dict[str, UpdaterFn] = {
    "projectile_path": updater_projectile_path,
}
