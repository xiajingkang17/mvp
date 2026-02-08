from __future__ import annotations

import pytest


def test_actions_module_imports_without_manim():
    pytest.importorskip("manim")
    from render.actions import ActionEngine  # noqa: F401

