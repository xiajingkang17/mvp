from manim import *
import numpy as np
import unicodedata


def reset_scene(scene, objects):
    """Default scene boundary behavior: clear all prior mobjects and shared registries."""
    scene.clear()
    objects.clear()
    if hasattr(scene, "scene_state"):
        scene.scene_state.clear()
    if hasattr(scene, "motion_cache"):
        scene.motion_cache.clear()


def prepare_scene_entry(scene, objects, keep_ids):
    """Reconcile current on-screen objects to the exact scene entry set."""
    keep = set(keep_ids)
    for obj_id in list(objects.keys()):
        if obj_id not in keep:
            mob = objects.get(obj_id)
            if mob is not None and mob in scene.mobjects:
                scene.remove(mob)
            objects.pop(obj_id, None)
    if "current_subtitle" not in keep:
        subtitle = objects.get("current_subtitle")
        if subtitle is not None and subtitle in scene.mobjects:
            scene.remove(subtitle)
        objects.pop("current_subtitle", None)
    if hasattr(scene, "scene_state"):
        scene.scene_state.clear()
    if hasattr(scene, "motion_cache"):
        scene.motion_cache.clear()


def _normalize_zone_rect(zone_rect):
    """
    Accept either normalized `(0..1)` zone rects or Manim world coordinates.
    """
    if len(zone_rect) != 4:
        raise ValueError("zone_rect must be (x0, x1, y0, y1)")
    x0, x1, y0, y1 = zone_rect
    x0, x1, y0, y1 = float(x0), float(x1), float(y0), float(y1)
    if 0.0 <= x0 <= 1.0 and 0.0 <= x1 <= 1.0 and 0.0 <= y0 <= 1.0 and 0.0 <= y1 <= 1.0:
        frame_w = float(config.frame_width)
        frame_h = float(config.frame_height)
        x0 = x0 * frame_w - frame_w / 2.0
        x1 = x1 * frame_w - frame_w / 2.0
        y0 = y0 * frame_h - frame_h / 2.0
        y1 = y1 * frame_h - frame_h / 2.0
    return x0, x1, y0, y1


def fit_in_zone(mobject, zone_rect, width_ratio=0.92, height_ratio=0.92):
    """Scale object to fit inside the target zone."""
    x0, x1, y0, y1 = _normalize_zone_rect(zone_rect)
    max_w = (x1 - x0) * width_ratio
    max_h = (y1 - y0) * height_ratio
    if mobject.width > max_w:
        mobject.scale_to_fit_width(max_w)
    if mobject.height > max_h:
        mobject.scale_to_fit_height(max_h)
    return mobject


def place_in_zone(mobject, zone_rect, offset=ORIGIN):
    """Place object at the zone center with optional offset."""
    x0, x1, y0, y1 = _normalize_zone_rect(zone_rect)
    center = np.array([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    offset_arr = np.array(offset, dtype=float)
    if offset_arr.shape == (2,):
        offset_arr = np.array([offset_arr[0], offset_arr[1], 0.0])
    elif offset_arr.shape != (3,):
        raise ValueError("offset must be a 2D or 3D vector")
    mobject.move_to(center + offset_arr)
    return mobject


def layout_formula_group(formulas, zone_rect):
    """Stack formulas vertically and place the group inside a formula zone rect."""
    group = VGroup(*formulas).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
    fit_in_zone(group, zone_rect, width_ratio=0.92, height_ratio=0.92)
    place_in_zone(group, zone_rect)
    return group


def register_obj(scene, objects, obj_id, mobject):
    """Register a stable object id and retire any old object under the same id."""
    old = objects.get(obj_id)
    if old is not None and old is not mobject:
        if old in scene.mobjects:
            scene.remove(old)
        try:
            old.clear_updaters()
        except Exception:
            pass
    objects[obj_id] = mobject
    return mobject


def _purge_registered_objects(scene, objects, obj_ids, animation_cls=FadeOut, run_time=0.25):
    """Remove a batch of registered objects in a single scene transition."""
    tracked_ids = []
    batch = []
    seen = set()

    for obj_id in obj_ids:
        mob = objects.get(obj_id)
        if mob is None:
            objects.pop(obj_id, None)
            continue
        tracked_ids.append(obj_id)
        mob_key = id(mob)
        if mob in scene.mobjects and mob_key not in seen:
            batch.append(mob)
            seen.add(mob_key)

    if batch:
        if animation_cls is None or run_time <= 0:
            scene.remove(*batch)
        else:
            scene.play(
                AnimationGroup(*(animation_cls(mob) for mob in batch), lag_ratio=0.0),
                run_time=run_time,
            )
            scene.remove(*batch)

    for obj_id in tracked_ids:
        mob = objects.pop(obj_id, None)
        if mob is not None:
            try:
                mob.clear_updaters()
            except Exception:
                pass


def remove_registered_obj(scene, objects, obj_id, animation_cls=FadeOut):
    """Remove and unregister a single object."""
    _purge_registered_objects(scene, objects, [obj_id], animation_cls=animation_cls, run_time=0.25)


def cleanup_step(scene, objects, keep_ids):
    """Remove every registered object that is not listed in keep_ids."""
    keep = set(keep_ids)
    to_remove = [obj_id for obj_id in list(objects.keys()) if obj_id not in keep]
    _purge_registered_objects(scene, objects, to_remove, animation_cls=FadeOut, run_time=0.2)


def cleanup_scene(scene, objects, keep_ids):
    """Keep only the exact scene exit set."""
    keep = set(keep_ids)
    to_remove = [obj_id for obj_id in list(objects.keys()) if obj_id not in keep]
    _purge_registered_objects(scene, objects, to_remove, animation_cls=FadeOut, run_time=0.2)


def _subtitle_visual_units(ch):
    if ch.isspace():
        return 0.35
    return 1.0 if unicodedata.east_asian_width(ch) in {"W", "F"} else 0.6


def _wrap_subtitle_text(text, *, max_units_per_line=30.0, max_lines=2):
    lines = []
    current = []
    current_units = 0.0

    for ch in str(text).strip():
        if ch == "\n":
            lines.append("".join(current).strip())
            current = []
            current_units = 0.0
            continue

        units = _subtitle_visual_units(ch)
        if current and current_units + units > max_units_per_line:
            lines.append("".join(current).strip())
            current = [ch]
            current_units = units
        else:
            current.append(ch)
            current_units += units

    if current:
        lines.append("".join(current).strip())

    lines = [line for line in lines if line]
    if not lines:
        return [""]
    if len(lines) > max_lines:
        raise ValueError("Subtitle text is too long for the reserved subtitle zone; split the step narration.")
    return lines


def _subtitle_scale_factor(text, subtitle_zone_rect):
    lines = _wrap_subtitle_text(text)
    subtitle = Text("\n".join(lines), font_size=28, color=WHITE)
    x0, x1, y0, y1 = _normalize_zone_rect(subtitle_zone_rect)
    max_w = (x1 - x0) * 0.96
    max_h = (y1 - y0) * 0.88

    scale_factor = 1.0
    if subtitle.width > 0:
        scale_factor = min(scale_factor, max_w / subtitle.width)
    if subtitle.height > 0:
        scale_factor = min(scale_factor, max_h / subtitle.height)
    return scale_factor


def _subtitle_can_render(text, subtitle_zone_rect):
    try:
        return _subtitle_scale_factor(text, subtitle_zone_rect) >= 0.94
    except ValueError:
        return False


def _estimate_subtitle_read_seconds(text):
    raw = str(text or "").strip()
    if not raw:
        return 0.0
    visual_units = sum(_subtitle_visual_units(ch) for ch in raw)
    return max(1.2, visual_units / 4.2 + 0.4)


def _split_subtitle_by_punctuation(text):
    punctuation = "，。；：？！,.!?;:"
    clauses = []
    current = []
    for ch in str(text).strip():
        current.append(ch)
        if ch in punctuation:
            clause = "".join(current).strip()
            if clause:
                clauses.append(clause)
            current = []
    tail = "".join(current).strip()
    if tail:
        clauses.append(tail)
    return clauses or [str(text).strip()]


def _split_subtitle_hard(text):
    raw = str(text).strip()
    if len(raw) <= 1:
        return [raw] if raw else []

    total_units = sum(_subtitle_visual_units(ch) for ch in raw)
    target = total_units / 2.0
    acc = 0.0
    split_at = 0
    for idx, ch in enumerate(raw, start=1):
        acc += _subtitle_visual_units(ch)
        if acc >= target:
            split_at = idx
            break

    split_at = max(1, min(split_at or (len(raw) // 2), len(raw) - 1))
    left = raw[:split_at].strip()
    right = raw[split_at:].strip()
    return [part for part in (left, right) if part]


def _normalize_runtime_subtitle_segments(text, subtitle_zone_rect):
    raw = str(text or "").strip()
    if not raw:
        return []
    if _subtitle_can_render(raw, subtitle_zone_rect):
        return [raw]

    clauses = _split_subtitle_by_punctuation(raw)
    if len(clauses) > 1:
        packed = []
        buffer = ""
        for clause in clauses:
            candidate = f"{buffer}{clause}".strip() if not buffer else f"{buffer}{clause}"
            if buffer and not _subtitle_can_render(candidate, subtitle_zone_rect):
                packed.extend(_normalize_runtime_subtitle_segments(buffer, subtitle_zone_rect))
                buffer = clause.strip()
            else:
                buffer = candidate.strip()
        if buffer:
            packed.extend(_normalize_runtime_subtitle_segments(buffer, subtitle_zone_rect))
        if packed:
            return packed

    parts = _split_subtitle_hard(raw)
    if len(parts) <= 1:
        return [raw]

    segments = []
    for part in parts:
        segments.extend(_normalize_runtime_subtitle_segments(part, subtitle_zone_rect))
    return segments


def show_subtitle(scene, objects, text, subtitle_zone_rect):
    """Render narration into a fixed reserved subtitle zone without shrinking it away."""
    old = objects.get("current_subtitle")
    if old is not None:
        scene.remove(old)
        objects.pop("current_subtitle", None)

    lines = _wrap_subtitle_text(text)
    subtitle = Text("\n".join(lines), font_size=28, color=WHITE)
    scale_factor = _subtitle_scale_factor(text, subtitle_zone_rect)

    if scale_factor < 0.94:
        raise ValueError("Subtitle text does not fit the fixed subtitle zone; split the narration into shorter steps.")
    if scale_factor < 1.0:
        subtitle.scale(scale_factor)

    place_in_zone(subtitle, subtitle_zone_rect)
    scene.add(subtitle)
    objects["current_subtitle"] = subtitle
    return subtitle


def run_step(scene, objects, subtitle_text, subtitle_zone_rect, keep_ids, step_fn):
    """
    Recommended execution order:
    1. normalize subtitle_text into runtime-safe subtitle segments
    2. show_subtitle(the first subtitle segment)
    2. execute create/update/remove logic in step_fn
    3. if there are remaining subtitle segments, show them sequentially
    4. cleanup_step(... keep ...)
    """
    text = str(subtitle_text or "").strip()
    raw_segments = [text] if text else []

    segments = []
    for raw in raw_segments:
        segments.extend(_normalize_runtime_subtitle_segments(raw, subtitle_zone_rect))

    if segments:
        start_time = float(getattr(scene, "time", 0.0))
        show_subtitle(scene, objects, segments[0], subtitle_zone_rect)
    else:
        start_time = float(getattr(scene, "time", 0.0))
    step_fn()
    if segments:
        elapsed = max(0.0, float(getattr(scene, "time", 0.0)) - start_time)
        remaining = _estimate_subtitle_read_seconds(segments[0]) - elapsed
        if remaining > 0:
            scene.wait(remaining)
    for segment in segments[1:]:
        show_subtitle(scene, objects, segment, subtitle_zone_rect)
        scene.wait(_estimate_subtitle_read_seconds(segment))
    cleanup_step(scene, objects, keep_ids)
