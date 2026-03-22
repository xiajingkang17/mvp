#!/usr/bin/env python3
"""
纯静态布局求解器。

输入是 static_code_parser.py 产出的 step 级 AST 数据，
输出是符合 Vision Agent 训练格式所需的：
- scene.objects
- scene.relations
- scene.prev_layout
- gt_layout

这里的 bbox 是基于代码语义与启发式规则求得的静态近似框，
不是运行渲染器得到的像素真值框。
"""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


FRAME_WIDTH = 14.0
FRAME_HEIGHT = 8.0
FRAME_LEFT = -FRAME_WIDTH / 2
FRAME_RIGHT = FRAME_WIDTH / 2
FRAME_TOP = FRAME_HEIGHT / 2
FRAME_BOTTOM = -FRAME_HEIGHT / 2


CONSTANTS: Dict[str, Any] = {
    "FRAME_WIDTH": FRAME_WIDTH,
    "FRAME_HEIGHT": FRAME_HEIGHT,
    "ORIGIN": (0.0, 0.0),
    "LEFT": (-1.0, 0.0),
    "RIGHT": (1.0, 0.0),
    "UP": (0.0, 1.0),
    "DOWN": (0.0, -1.0),
    "UL": (-1.0, 1.0),
    "UR": (1.0, 1.0),
    "DL": (-1.0, -1.0),
    "DR": (1.0, -1.0),
    "SMALL_BUFF": 0.1,
    "MED_SMALL_BUFF": 0.15,
    "MED_LARGE_BUFF": 0.35,
    "LARGE_BUFF": 0.5,
    "DEFAULT_MOBJECT_TO_MOBJECT_BUFFER": 0.25,
    "DEGREES": math.pi / 180.0,
    "PI": math.pi,
    "TAU": math.tau,
}


@dataclass
class BBox:
    cx: float
    cy: float
    w: float
    h: float

    def normalized(self) -> List[float]:
        return [
            round((self.cx - FRAME_LEFT) / FRAME_WIDTH, 6),
            round((FRAME_TOP - self.cy) / FRAME_HEIGHT, 6),
            round(max(min(self.w / FRAME_WIDTH, 1.0), 0.01), 6),
            round(max(min(self.h / FRAME_HEIGHT, 1.0), 0.01), 6),
        ]


def bbox_union(boxes: Iterable[BBox]) -> Optional[BBox]:
    boxes = list(boxes)
    if not boxes:
        return None
    left = min(box.cx - box.w / 2 for box in boxes)
    right = max(box.cx + box.w / 2 for box in boxes)
    top = max(box.cy + box.h / 2 for box in boxes)
    bottom = min(box.cy - box.h / 2 for box in boxes)
    return BBox(
        cx=(left + right) / 2,
        cy=(top + bottom) / 2,
        w=max(right - left, 0.1),
        h=max(top - bottom, 0.1),
    )


class SafeEvaluator(ast.NodeVisitor):
    """仅支持数值/向量常量的表达式求值器。"""

    def __init__(self, env: Dict[str, Any]):
        self.env = env

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.env:
            return self.env[node.id]
        raise ValueError(node.id)

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_List(self, node: ast.List) -> Any:
        return [self.visit(elt) for elt in node.elts]

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(type(node.op).__name__)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return _add_values(left, right)
        if isinstance(node.op, ast.Sub):
            return _sub_values(left, right)
        if isinstance(node.op, ast.Mult):
            return _mul_values(left, right)
        if isinstance(node.op, ast.Div):
            return _div_values(left, right)
        if isinstance(node.op, ast.Pow):
            return left ** right
        raise ValueError(type(node.op).__name__)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(type(node).__name__)


def _add_values(left: Any, right: Any) -> Any:
    if isinstance(left, tuple) and isinstance(right, tuple) and len(left) == len(right):
        return tuple(a + b for a, b in zip(left, right))
    return left + right


def _sub_values(left: Any, right: Any) -> Any:
    if isinstance(left, tuple) and isinstance(right, tuple) and len(left) == len(right):
        return tuple(a - b for a, b in zip(left, right))
    return left - right


def _mul_values(left: Any, right: Any) -> Any:
    if isinstance(left, tuple) and isinstance(right, (int, float)):
        return tuple(a * right for a in left)
    if isinstance(right, tuple) and isinstance(left, (int, float)):
        return tuple(left * a for a in right)
    return left * right


def _div_values(left: Any, right: Any) -> Any:
    if isinstance(left, tuple) and isinstance(right, (int, float)):
        return tuple(a / right for a in left)
    return left / right


def safe_eval(expr: str, env: Optional[Dict[str, Any]] = None) -> Any:
    env = {**CONSTANTS, **(env or {})}
    tree = ast.parse(expr, mode="eval")
    return SafeEvaluator(env).visit(tree)


def parse_arguments(arguments: List[str]) -> Tuple[List[str], Dict[str, str]]:
    positional: List[str] = []
    kwargs: Dict[str, str] = {}
    for arg in arguments:
        if "=" in arg and not arg.startswith(("==", "!=", "<=", ">=")):
            key, value = arg.split("=", 1)
            kwargs[key.strip()] = value.strip()
        else:
            positional.append(arg.strip())
    return positional, kwargs


def extract_literal_text(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def looks_like_ref(value: str) -> bool:
    if not value:
        return False
    blocked = ("<", "[", "{", "(", "'", '"')
    return not value.startswith(blocked)


def strip_star(value: str) -> str:
    return value[1:] if value.startswith("*") else value


def vector_from_text(value: str, env: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    value = value.strip()
    if not value:
        return None
    try:
        result = safe_eval(value, env)
    except Exception:
        return None
    if isinstance(result, (list, tuple)) and len(result) >= 2:
        return (float(result[0]), float(result[1]))
    return None


def number_from_text(value: Optional[str], env: Dict[str, Any], default: float) -> float:
    if not value:
        return default
    try:
        result = safe_eval(value, env)
    except Exception:
        return default
    if isinstance(result, (int, float)):
        return float(result)
    return default


def clamp_center(box: BBox) -> BBox:
    box.w = min(max(box.w, 0.1), FRAME_WIDTH)
    box.h = min(max(box.h, 0.1), FRAME_HEIGHT)
    half_w = max(box.w / 2, 0.05)
    half_h = max(box.h / 2, 0.05)
    box.cx = min(max(box.cx, FRAME_LEFT + half_w), FRAME_RIGHT - half_w)
    box.cy = min(max(box.cy, FRAME_BOTTOM + half_h), FRAME_TOP - half_h)
    return box


def infer_text_size(content: str, scale: float = 1.0) -> Tuple[float, float]:
    text = extract_literal_text(content)
    lines = [line for line in text.split("\\n") if line] or [text]
    max_chars = max((len(line) for line in lines), default=1)
    width = max(0.8, min(6.0, 0.16 * max_chars))
    height = max(0.4, min(3.0, 0.45 * len(lines)))
    return width * scale, height * scale


def infer_tex_size(content: str, scale: float = 1.0) -> Tuple[float, float]:
    text = extract_literal_text(content)
    line_count = max(text.count("\\\\") + 1, 1)
    token_count = max(len(text.replace("\\", " ").replace("{", " ").replace("}", " ").split()), 1)
    char_count = len(text)
    width = max(1.0, min(8.5, 0.07 * char_count + 0.16 * token_count))
    height = max(0.45, min(3.5, 0.4 * line_count + 0.012 * char_count))
    return width * scale, height * scale


def child_boxes_from_arguments(arguments: List[str], env: Dict[str, Any]) -> List[BBox]:
    boxes: List[BBox] = []
    for arg in arguments:
        ref = strip_star(arg)
        if ref in env.get("__state_boxes__", {}):
            boxes.append(env["__state_boxes__"][ref])
            continue
        if arg.startswith(("Text(", "Tex(", "OldTex(", "OldTexText(", "MathTex(")):
            obj_type, inner_args = split_call(arg)
            if obj_type:
                width, height = infer_size(obj_type, ", ".join(inner_args), inner_args, env.get("__state_boxes__", {}), env)
                boxes.append(BBox(0.0, 0.0, width, height))
    return boxes


def split_call(expr: str) -> Tuple[Optional[str], List[str]]:
    expr = expr.strip()
    if not expr.endswith(")") or "(" not in expr:
        return None, []
    name, rest = expr.split("(", 1)
    inner = rest[:-1]
    return name.strip(), split_top_level_args(inner)


def split_top_level_args(raw: str) -> List[str]:
    if not raw:
        return []
    args: List[str] = []
    current: List[str] = []
    depth = 0
    quote: Optional[str] = None
    escape = False
    for ch in raw:
        if quote:
            current.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            current.append(ch)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(depth - 1, 0)
        if ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        args.append(tail)
    return args


def infer_size(
    object_type: str,
    content: str,
    arguments: List[str],
    state_boxes: Dict[str, BBox],
    env: Dict[str, Any],
) -> Tuple[float, float]:
    positional, kwargs = parse_arguments(arguments)
    lower_type = object_type.lower()
    font_size = number_from_text(kwargs.get("font_size"), env, 48.0)
    text_scale = max(font_size / 48.0, 0.6)

    if object_type in {"Text", "Tex", "OldTex", "OldTexText", "MathTex", "Integer"}:
        scale = number_from_text(kwargs.get("scale"), env, 1.0) * text_scale
        payload = content or (", ".join(positional) if positional else object_type)
        if object_type in {"Tex", "OldTex", "MathTex"}:
            return infer_tex_size(payload, scale)
        if object_type == "OldTexText":
            return infer_text_size(payload.replace("', '", "\\n"), scale)
        return infer_text_size(payload, scale)

    if object_type == "Circle":
        radius = number_from_text(kwargs.get("radius"), env, 1.0)
        return 2 * radius, 2 * radius

    if object_type == "Square":
        side = number_from_text(kwargs.get("side_length"), env, 2.0)
        return side, side

    if object_type in {"Rectangle", "SurroundingRectangle"}:
        width = number_from_text(kwargs.get("width"), env, 3.0)
        height = number_from_text(kwargs.get("height"), env, 1.6)
        if object_type == "SurroundingRectangle" and positional:
            target = state_boxes.get(strip_star(positional[0]))
            if target:
                buff = number_from_text(kwargs.get("buff"), env, 0.2)
                return target.w + 2 * buff, target.h + 2 * buff
        return width, height

    if object_type == "Line":
        if len(positional) >= 2:
            start = vector_from_text(positional[0], env)
            end = vector_from_text(positional[1], env)
            if start and end:
                return max(abs(end[0] - start[0]), 0.1), max(abs(end[1] - start[1]), 0.1)
        return 2.5, 0.15

    if object_type in {"Arrow", "Vector"}:
        if positional:
            end = vector_from_text(positional[-1], env)
            if end:
                return max(abs(end[0]), 0.2), max(abs(end[1]), 0.2)
        return 2.0, 0.25

    if object_type == "Dot":
        radius = number_from_text(kwargs.get("radius"), env, 0.08)
        return max(2 * radius, 0.12), max(2 * radius, 0.12)

    if object_type in {"Axes", "ComplexPlane", "NumberPlane"}:
        width = number_from_text(kwargs.get("width"), env, 6.0)
        height = number_from_text(kwargs.get("height"), env, 4.0)
        if width == 6.0 and height != 4.0:
            width = min(height * 1.8, FRAME_WIDTH)
        elif height == 4.0 and width != 6.0:
            height = min(width / 1.8, FRAME_HEIGHT)
        return width, height

    if object_type == "NumberLine":
        width = number_from_text(kwargs.get("width"), env, 7.0)
        return width, 0.25

    if object_type == "Brace" and positional:
        target = state_boxes.get(strip_star(positional[0]))
        if not target:
            call_type, inner_args = split_call(positional[0])
            if call_type == "Line":
                line_w, line_h = infer_size("Line", positional[0], inner_args, state_boxes, env)
                target = BBox(0.0, 0.0, line_w, line_h)
        if target:
            direction = vector_from_text(positional[1], env) if len(positional) > 1 else CONSTANTS["UP"]
            if direction and abs(direction[0]) >= abs(direction[1]):
                return max(target.w * 0.25, 0.25), max(target.h, 0.4)
            return max(target.w, 0.4), max(target.h * 0.3, 0.25)
        return 2.0, 0.4

    if object_type in {"VGroup", "Group"}:
        refs = [state_boxes.get(strip_star(arg)) for arg in positional if strip_star(arg) in state_boxes]
        union = bbox_union(ref for ref in refs if ref is not None)
        if union:
            return union.w, union.h
        child_boxes = child_boxes_from_arguments(positional, {**env, "__state_boxes__": state_boxes})
        child_union = bbox_union(child_boxes)
        if child_union:
            return child_union.w, child_union.h
        if any("<GeneratorExp>" in arg for arg in positional):
            count = max(len(positional), 3)
            return min(1.2 * count, 6.0), 1.0
        return 3.0, 2.0

    if object_type in {"Polygon", "VMobject", "GlowDot"}:
        return 2.0, 2.0

    if "text" in lower_type:
        return infer_text_size(content, text_scale)
    if "plane" in lower_type:
        return 6.0, 4.0
    if "line" in lower_type:
        return 3.0, 0.2
    if "arrow" in lower_type:
        return 2.0, 0.25
    if "rect" in lower_type or "box" in lower_type:
        return 3.0, 1.6
    if "circle" in lower_type or "dot" in lower_type:
        return 1.0, 1.0

    return 2.0, 1.2


class StaticLayoutSolver:
    def __init__(self) -> None:
        self.active_objects: Dict[str, Dict[str, Any]] = {}
        self.boxes: Dict[str, BBox] = {}
        self.creation_order: List[str] = []
        self.default_cursor = 0

    def solve_scene(self, class_name: str, animation_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        self.active_objects.clear()
        self.boxes.clear()
        self.creation_order.clear()
        self.default_cursor = 0

        for step in animation_steps:
            record = self._solve_step(class_name, step)
            if record is not None:
                records.append(record)
        return records

    def _solve_step(self, class_name: str, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        step_id = step.get("step_id", 0)
        trigger = step.get("trigger", "")
        prior_objects = step.get("prior_objects", [])
        prior_relations = step.get("prior_relations", [])

        new_ids: List[str] = []
        for obj in prior_objects:
            obj_id = obj.get("variable_name", "")
            if not obj_id:
                continue
            if obj_id not in self.active_objects:
                self.creation_order.append(obj_id)
                new_ids.append(obj_id)
            self.active_objects[obj_id] = {
                "id": obj_id,
                "type": obj.get("object_type", ""),
                "content": ", ".join(obj.get("arguments", [])) if obj.get("arguments") else "",
                "raw_arguments": obj.get("arguments", []),
            }
            if obj_id not in self.boxes:
                self.boxes[obj_id] = self._initialize_bbox(self.active_objects[obj_id])

        for relation in prior_relations:
            self._apply_relation(relation)

        self._refresh_group_boxes()

        scene_objects: List[Dict[str, Any]] = []
        prev_layout: List[Dict[str, Any]] = []
        gt_layout: List[Dict[str, Any]] = []
        relation_entries = self._build_relations(prior_relations)

        for obj_id in self.creation_order:
            meta = self.active_objects[obj_id]
            status = "new" if obj_id in new_ids else "keep"
            scene_objects.append({
                "id": obj_id,
                "type": meta["type"],
                "content": meta["content"],
                "role": infer_role(meta["type"]),
                "status": status,
            })
            if status == "keep" and obj_id in self.boxes:
                prev_layout.append({
                    "id": obj_id,
                    "bbox": self.boxes[obj_id].normalized(),
                })
            gt_layout.append({
                "id": obj_id,
                "bbox": self.boxes[obj_id].normalized(),
            })

        if not scene_objects:
            return None

        return {
            "sample_id": f"{class_name}_{step_id}",
            "scene": {
                "scene_text": trigger,
                "objects": scene_objects,
                "relations": relation_entries,
                "prev_layout": prev_layout,
            },
            "gt_layout": gt_layout,
        }

    def _build_relations(self, prior_relations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        raw_entries = [
            entry for entry in (self._relation_to_entry(rel) for rel in prior_relations)
            if entry
        ]
        normalized = [self._normalize_relation(entry) for entry in raw_entries]
        supplemented = normalized + self._infer_inside_relations()
        deduped: List[Dict[str, str]] = []
        seen = set()
        for entry in supplemented:
            key = (entry["type"], entry["src"], entry["dst"])
            if key in seen or entry["src"] == entry["dst"]:
                continue
            seen.add(key)
            deduped.append(entry)
        return deduped

    def _initialize_bbox(self, meta: Dict[str, Any]) -> BBox:
        width, height = infer_size(
            meta["type"],
            meta["content"],
            meta.get("raw_arguments", []),
            self.boxes,
            self._env(),
        )
        col = self.default_cursor % 3
        row = self.default_cursor // 3
        self.default_cursor += 1
        cx = -3.5 + col * 3.0
        cy = 2.4 - row * 2.2
        return clamp_center(BBox(cx=cx, cy=cy, w=width, h=height))

    def _env(self) -> Dict[str, Any]:
        env: Dict[str, Any] = {}
        for obj_id, box in self.boxes.items():
            env[obj_id] = (box.cx, box.cy)
        return env

    def _apply_relation(self, relation: Dict[str, Any]) -> None:
        subject = relation.get("subject", "")
        action = relation.get("action", "")
        args = relation.get("args", [])
        kwargs = relation.get("kwargs", {})

        if subject not in self.boxes:
            return

        box = self.boxes[subject]
        env = self._env()

        if action == "scale":
            factor = number_from_text(args[0] if args else None, env, 1.0)
            box.w = max(box.w * factor, 0.1)
            box.h = max(box.h * factor, 0.1)

        elif action in {"set_width", "scale_to_fit_width", "stretch_to_fit_width", "match_width"}:
            if action == "match_width" and args and strip_star(args[0]) in self.boxes:
                box.w = self.boxes[strip_star(args[0])].w
            else:
                box.w = max(number_from_text(args[0] if args else kwargs.get("width"), env, box.w), 0.1)

        elif action in {"set_height", "scale_to_fit_height", "stretch_to_fit_height", "match_height"}:
            if action == "match_height" and args and strip_star(args[0]) in self.boxes:
                box.h = self.boxes[strip_star(args[0])].h
            else:
                box.h = max(number_from_text(args[0] if args else kwargs.get("height"), env, box.h), 0.1)

        elif action == "move_to":
            target = args[0] if args else None
            point = self._resolve_point_or_box_center(target, env)
            if point:
                box.cx, box.cy = point

        elif action == "shift":
            vector = vector_from_text(args[0], env) if args else None
            if vector:
                box.cx += vector[0]
                box.cy += vector[1]

        elif action == "to_edge":
            direction = vector_from_text(args[0], env) if args else None
            buff = number_from_text(args[1] if len(args) > 1 else kwargs.get("buff"), env, 0.25)
            if direction:
                self._place_on_edge(box, direction, buff)

        elif action == "to_corner":
            direction = vector_from_text(args[0], env) if args else None
            buff = number_from_text(args[1] if len(args) > 1 else kwargs.get("buff"), env, 0.25)
            if direction:
                self._place_on_corner(box, direction, buff)

        elif action == "center":
            box.cx = 0.0
            box.cy = 0.0

        elif action == "next_to":
            self._place_next_to(box, args, kwargs, env)

        elif action == "align_to":
            self._align_to(box, args, env)

        elif action == "surround":
            target = self.boxes.get(strip_star(args[0])) if args else None
            if target:
                buff = number_from_text(kwargs.get("buff"), env, 0.2)
                box.cx = target.cx
                box.cy = target.cy
                box.w = target.w + 2 * buff
                box.h = target.h + 2 * buff

        elif action in {"arrange", "arrange_in_grid"}:
            self._arrange_group(subject, action, args, kwargs, env)

        clamp_center(box)

    def _place_next_to(
        self,
        box: BBox,
        args: List[str],
        kwargs: Dict[str, str],
        env: Dict[str, Any],
    ) -> None:
        if not args:
            return
        target_id = strip_star(args[0])
        target = self.boxes.get(target_id)
        if not target:
            return
        direction = vector_from_text(args[1], env) if len(args) > 1 else CONSTANTS["RIGHT"]
        buff = number_from_text(args[2] if len(args) > 2 else kwargs.get("buff"), env, 0.25)
        if not direction:
            direction = CONSTANTS["RIGHT"]
        dx, dy = direction
        if abs(dx) >= abs(dy):
            sign = 1 if dx >= 0 else -1
            box.cx = target.cx + sign * (target.w / 2 + buff + box.w / 2)
            box.cy = target.cy
        else:
            sign = 1 if dy >= 0 else -1
            box.cx = target.cx
            box.cy = target.cy + sign * (target.h / 2 + buff + box.h / 2)

    def _align_to(self, box: BBox, args: List[str], env: Dict[str, Any]) -> None:
        if len(args) < 2:
            return
        target = self.boxes.get(strip_star(args[0]))
        edge = vector_from_text(args[1], env)
        if not target or not edge:
            return
        dx, dy = edge
        if abs(dx) >= abs(dy):
            if dx >= 0:
                box.cx = target.cx + target.w / 2 - box.w / 2
            else:
                box.cx = target.cx - target.w / 2 + box.w / 2
        else:
            if dy >= 0:
                box.cy = target.cy + target.h / 2 - box.h / 2
            else:
                box.cy = target.cy - target.h / 2 + box.h / 2

    def _arrange_group(
        self,
        subject: str,
        action: str,
        args: List[str],
        kwargs: Dict[str, str],
        env: Dict[str, Any],
    ) -> None:
        refs = self._group_refs(subject)
        if len(refs) < 2:
            return

        if action == "arrange_in_grid":
            cols = int(number_from_text(kwargs.get("n_cols"), env, 2))
            buff = number_from_text(kwargs.get("buff"), env, 0.25)
            for idx, ref in enumerate(refs):
                row = idx // cols
                col = idx % cols
                box = self.boxes[ref]
                box.cx = -2.5 + col * (box.w + buff)
                box.cy = 2.0 - row * (box.h + buff)
                clamp_center(box)
            return

        direction = vector_from_text(args[0], env) if args else CONSTANTS["RIGHT"]
        if not direction:
            direction = CONSTANTS["RIGHT"]
        buff = number_from_text(args[1] if len(args) > 1 else kwargs.get("buff"), env, 0.25)
        prev = self.boxes[refs[0]]
        for ref in refs[1:]:
            current = self.boxes[ref]
            if abs(direction[0]) >= abs(direction[1]):
                sign = 1 if direction[0] >= 0 else -1
                current.cx = prev.cx + sign * (prev.w / 2 + buff + current.w / 2)
                current.cy = prev.cy
            else:
                sign = 1 if direction[1] >= 0 else -1
                current.cx = prev.cx
                current.cy = prev.cy + sign * (prev.h / 2 + buff + current.h / 2)
            clamp_center(current)
            prev = current

    def _group_refs(self, subject: str) -> List[str]:
        meta = self.active_objects.get(subject, {})
        arguments = meta.get("raw_arguments", [])
        refs = []
        for arg in arguments:
            ref = strip_star(arg)
            if ref in self.boxes:
                refs.append(ref)
        return refs

    def _place_on_edge(self, box: BBox, direction: Tuple[float, float], buff: float) -> None:
        dx, dy = direction
        if abs(dx) >= abs(dy):
            box.cx = FRAME_RIGHT - box.w / 2 - buff if dx >= 0 else FRAME_LEFT + box.w / 2 + buff
        else:
            box.cy = FRAME_TOP - box.h / 2 - buff if dy >= 0 else FRAME_BOTTOM + box.h / 2 + buff

    def _place_on_corner(self, box: BBox, direction: Tuple[float, float], buff: float) -> None:
        self._place_on_edge(box, (direction[0], 0.0), buff)
        self._place_on_edge(box, (0.0, direction[1]), buff)

    def _resolve_point_or_box_center(
        self,
        target: Optional[str],
        env: Dict[str, Any],
    ) -> Optional[Tuple[float, float]]:
        if not target:
            return None
        ref = strip_star(target)
        if ref in self.boxes:
            box = self.boxes[ref]
            return (box.cx, box.cy)
        return vector_from_text(target, env)

    def _refresh_group_boxes(self) -> None:
        for obj_id, meta in self.active_objects.items():
            if meta["type"] not in {"VGroup", "Group"}:
                continue
            refs = self._group_refs(obj_id)
            union = bbox_union(self.boxes[ref] for ref in refs if ref in self.boxes)
            if union:
                self.boxes[obj_id] = clamp_center(union)

    def _relation_to_entry(self, relation: Dict[str, Any]) -> Optional[Dict[str, str]]:
        subject = relation.get("subject", "")
        action = relation.get("action", "")
        args = relation.get("args", [])
        env = self._env()

        if action == "next_to" and args:
            target = strip_star(args[0])
            direction = vector_from_text(args[1], env) if len(args) > 1 else CONSTANTS["RIGHT"]
            if target in self.active_objects and direction:
                if abs(direction[0]) >= abs(direction[1]):
                    rel_type = "right_of" if direction[0] >= 0 else "left_of"
                else:
                    rel_type = "above" if direction[1] >= 0 else "below"
                return {"type": rel_type, "src": subject, "dst": target}

        if action == "align_to" and args and strip_star(args[0]) in self.active_objects:
            return {"type": "aligned_with", "src": subject, "dst": strip_star(args[0])}

        if action == "move_to" and args and strip_star(args[0]) in self.active_objects:
            return {"type": "centered_on", "src": subject, "dst": strip_star(args[0])}

        if action == "surround" and args and strip_star(args[0]) in self.active_objects:
            return {"type": "around", "src": subject, "dst": strip_star(args[0])}

        return None

    def _normalize_relation(self, entry: Dict[str, str]) -> Dict[str, str]:
        rel_type = entry["type"]
        src = entry["src"]
        dst = entry["dst"]
        if rel_type == "below":
            return {"type": "above", "src": dst, "dst": src}
        if rel_type == "right_of":
            return {"type": "left_of", "src": dst, "dst": src}
        return entry

    def _infer_inside_relations(self) -> List[Dict[str, str]]:
        relations: List[Dict[str, str]] = []
        ids = list(self.active_objects.keys())
        for src_id in ids:
            src_box = self.boxes.get(src_id)
            if not src_box:
                continue
            for dst_id in ids:
                if src_id == dst_id:
                    continue
                dst_box = self.boxes.get(dst_id)
                if not dst_box:
                    continue
                dst_meta = self.active_objects[dst_id]
                dst_role = infer_role(dst_meta["type"])
                if dst_role not in {"coordinate_system", "container", "panel"}:
                    continue
                if src_box.w > dst_box.w * 0.92 or src_box.h > dst_box.h * 0.92:
                    continue
                if dst_role == "coordinate_system" and infer_role(self.active_objects[src_id]["type"]) in {"title", "annotation"}:
                    continue
                if _is_inside(src_box, dst_box):
                    relations.append({"type": "inside", "src": src_id, "dst": dst_id})
        return relations


def infer_role(object_type: str) -> str:
    lower = object_type.lower()
    if object_type in {"Text", "OldTexText"}:
        return "title"
    if object_type in {"Tex", "OldTex", "MathTex", "Integer"}:
        return "equation"
    if object_type in {"Axes", "ComplexPlane", "NumberPlane", "NumberLine"}:
        return "coordinate_system"
    if object_type in {"Brace"} or "brace" in lower or "label" in lower:
        return "annotation"
    if object_type in {"VGroup", "Group"}:
        return "group"
    if object_type in {"SurroundingRectangle"}:
        return "container"
    if object_type in {"Rectangle"}:
        return "panel"
    if object_type in {"Arrow", "Vector"} or "arrow" in lower or "vector" in lower:
        return "vector"
    if "bar" in lower:
        return "bar"
    if "graph" in lower or "curve" in lower or "wave" in lower or object_type in {"VMobject"}:
        return "curve"
    if object_type in {"Circle", "Polygon", "Line", "Dot", "GlowDot"}:
        return "main_figure"
    return "geometric_shape"


def _is_inside(inner: BBox, outer: BBox, margin: float = 0.01) -> bool:
    inner_left = inner.cx - inner.w / 2
    inner_right = inner.cx + inner.w / 2
    inner_top = inner.cy + inner.h / 2
    inner_bottom = inner.cy - inner.h / 2

    outer_left = outer.cx - outer.w / 2
    outer_right = outer.cx + outer.w / 2
    outer_top = outer.cy + outer.h / 2
    outer_bottom = outer.cy - outer.h / 2

    return (
        inner_left >= outer_left - margin and
        inner_right <= outer_right + margin and
        inner_bottom >= outer_bottom - margin and
        inner_top <= outer_top + margin and
        inner.w <= outer.w and
        inner.h <= outer.h
    )


def solve_ast_dataset(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    solver = StaticLayoutSolver()
    records: List[Dict[str, Any]] = []
    for class_name, scene_data in ast_data.get("scenes", {}).items():
        records.extend(solver.solve_scene(class_name, scene_data.get("animation_steps", [])))
    return records
