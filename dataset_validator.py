#!/usr/bin/env python3
"""校验生成的数据集是否满足 vision_agent_training_format.md 的结构要求。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def validate_dataset(dataset_path: str) -> Dict[str, int]:
    stats = {
        "records": 0,
        "missing_scene": 0,
        "missing_gt_layout": 0,
        "id_order_mismatch": 0,
        "invalid_bbox": 0,
        "invalid_prev_bbox": 0,
        "empty_objects": 0,
    }

    path = Path(dataset_path)
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            stats["records"] += 1
            record = json.loads(line)
            scene = record.get("scene")
            if scene is None:
                stats["missing_scene"] += 1
                continue
            gt_layout = record.get("gt_layout")
            if gt_layout is None:
                stats["missing_gt_layout"] += 1
                continue

            objects = scene.get("objects", [])
            prev_layout = scene.get("prev_layout", [])
            if not objects:
                stats["empty_objects"] += 1

            object_ids = [obj.get("id") for obj in objects]
            gt_ids = [item.get("id") for item in gt_layout]
            if object_ids != gt_ids:
                stats["id_order_mismatch"] += 1

            stats["invalid_bbox"] += _count_invalid_boxes(gt_layout)
            stats["invalid_prev_bbox"] += _count_invalid_boxes(prev_layout)

    return stats


def _count_invalid_boxes(items: List[Dict[str, object]]) -> int:
    invalid = 0
    for item in items:
        bbox = item.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            invalid += 1
            continue
        if any(not isinstance(value, (int, float)) for value in bbox):
            invalid += 1
            continue
        if any(value < 0 or value > 1 for value in bbox):
            invalid += 1
    return invalid


def main() -> None:
    dataset_path = "/Users/chenshutong/Desktop/3b1b/master_dataset.jsonl"
    print(validate_dataset(dataset_path))


if __name__ == "__main__":
    main()
