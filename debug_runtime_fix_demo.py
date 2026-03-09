from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    repo_text = str(REPO_ROOT)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)

from Manim4Teach.pipeline.stage2.runtime_fix import summarize_runtime_error


TRACEBACK_TEXT = r'''
Traceback (most recent call last):
  File "scene.py", line 137, in construct
    self.play(FadeOut(VGroup(*self.mobjects)))
TypeError: Only values of type VMobject can be added as submobjects of VGroup, but the value Mobject is of type Mobject. You can try adding this value into a Group instead.
'''


def main() -> None:
    preview_report = {
        "ok": False,
        "render": {
            "stdout_tail": "",
            "stderr_tail": TRACEBACK_TEXT,
        },
    }
    summary = summarize_runtime_error(preview_report=preview_report)
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
