from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from manim import Scene

from examples.templates.preview_utils import add_template_preview


class PreviewLeft4Right4(Scene):
    def construct(self):
        add_template_preview(self, "left4_right4")
