from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("manim")
from manim import Dot, ValueTracker

from render.actions import ActionEngine
from render.runtime_state import RuntimeState
from schema.scene_plan_models import PlayAction, WaitAction


class _DummyScene:
    def __init__(self):
        self.play_calls = []
        self.wait_calls = []

    def play(self, *anims, **kwargs):
        self.play_calls.append((anims, kwargs))

    def wait(self, duration):
        self.wait_calls.append(duration)


def _ctx(default_duration: float = 1.0):
    return SimpleNamespace(defaults=SimpleNamespace(action_duration=default_duration))


def test_wait_action_advances_timeline_clock():
    scene = _DummyScene()
    state = RuntimeState(timeline_clock=ValueTracker(0.0))
    engine = ActionEngine(scene=scene, state=state, ctx=_ctx())

    action = WaitAction(op="wait", duration=1.5)
    engine.run_action(action)

    assert len(scene.play_calls) == 1
    assert scene.wait_calls == []
    assert state.timeline_seconds == pytest.approx(1.5, abs=1e-9)


def test_play_action_advances_timeline_clock():
    scene = _DummyScene()
    state = RuntimeState(
        objects={"o1": Dot()},
        timeline_clock=ValueTracker(0.0),
    )
    engine = ActionEngine(scene=scene, state=state, ctx=_ctx(default_duration=1.0))

    action = PlayAction(op="play", anim="fade_in", targets=["o1"], duration=2.0)
    result = engine.run_action(action)

    assert len(scene.play_calls) == 1
    assert scene.wait_calls == []
    assert state.timeline_seconds == pytest.approx(2.0, abs=1e-9)
    assert "o1" in result.newly_visible
