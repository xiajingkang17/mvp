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
─────────────────────────────── Traceback (most recent call last) ────────────────────────────────╮
│ E:\anaconda\anacondainstall\envs\Manimpy\lib\site-packages\manim\cli\render\commands.py:125 in   │
│ render                                                                                           │
│                                                                                                  │
│   122 │   │   │   try:                                                                           │
│   123 │   │   │   │   with tempconfig({}):                                                       │
│   124 │   │   │   │   │   scene = SceneClass()                                                   │
│ ❱ 125 │   │   │   │   │   scene.render()                                                         │
│   126 │   │   │   except Exception:                                                              │
│   127 │   │   │   │   error_console.print_exception()                                            │
│   128 │   │   │   │   sys.exit(1)                                                                │
│                                                                                                  │
│ E:\anaconda\anacondainstall\envs\Manimpy\lib\site-packages\manim\scene\scene.py:260 in render    │
│                                                                                                  │
│    257 │   │   """                                                                               │
│    258 │   │   self.setup()                                                                      │
│    259 │   │   try:                                                                              │
│ ❱  260 │   │   │   self.construct()                                                              │
│    261 │   │   except EndSceneEarlyException:                                                    │
│    262 │   │   │   pass                                                                          │
│    263 │   │   except RerunSceneException:                                                       │
│                                                                                                  │
│ E:\AI4Learning-Backend\manim\test.py:137 in construct                                            │
│                                                                                                  │
│   134 │   │   self.play(Write(summary))                                                          │
│   135 │   │   self.wait(2)                                                                       │
│   136 │   │                                                                                      │
│ ❱ 137 │   │   self.play(FadeOut(VGroup(*self.mobjects)))                                         │
│   138                                                                                            │
│                                                                                                  │
│ E:\anaconda\anacondainstall\envs\Manimpy\lib\site-packages\manim\mobject\types\vectorized_mobjec │
│ t.py:2140 in __init__                                                                            │
│                                                                                                  │
│   2137 │   │   self, *vmobjects: VMobject | Iterable[VMobject], **kwargs: Any                    │
│   2138 │   ) -> None:                                                                            │
│   2139 │   │   super().__init__(**kwargs)                                                        │
│ ❱ 2140 │   │   self.add(*vmobjects)                                                              │
│   2141 │                                                                                         │
│   2142 │   def __repr__(self) -> str:                                                            │
│   2143 │   │   return f"{self.__class__.__name__}({', '.join(str(mob) for mob in self.submobjec  │
│                                                                                                  │
│ E:\anaconda\anacondainstall\envs\Manimpy\lib\site-packages\manim\mobject\types\vectorized_mobjec │
│ t.py:2255 in add                                                                                 │
│                                                                                                  │
│   2252 │   │   │   elif isinstance(vmobject, Iterable) and isinstance(                           │
│   2253 │   │   │   │   vmobject, (Mobject, OpenGLMobject)                                        │
│   2254 │   │   │   ):                                                                            │
│ ❱ 2255 │   │   │   │   raise TypeError(                                                          │
│   2256 │   │   │   │   │   f"{get_type_error_message(vmobject, (i, 0))} "                        │
│   2257 │   │   │   │   │   "You can try adding this value into a Group instead."                 │
│   2258 │   │   │   │   )                                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
TypeError: Only values of type VMobject can be added as submobjects of VGroup, but the value Mobject (at
index 0 of parameter 1) is of type Mobject. You can try adding this value into a Group instead.
'''


def main() -> None:
    static_report = {
        "compile_ok": True,
        "compile_error": "",
    }
    preview_report = {
        "ok": False,
        "render": {
            "stdout_tail": "",
            "stderr_tail": TRACEBACK_TEXT,
        },
    }
    summary = summarize_runtime_error(
        static_report=static_report,
        preview_report=preview_report,
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
