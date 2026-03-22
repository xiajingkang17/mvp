from manimlib import *


class AnimatedStreamLines(VGroup):
    def __init__(
        self,
        stream_lines,
        lag_range=4,
        rate_multiple=1.0,
        line_anim_config=None,
        semantic_type="vector_field",
        semantic_role="stream_lines_animation",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.stream_lines = stream_lines
        self.lag_range = float(lag_range)
        self.rate_multiple = float(rate_multiple)
        self.line_anim_config = dict(line_anim_config or {})

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.time = 0.0
        self._build_animated_lines()
        self.add(self.stream_lines, self.animated_lines)

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        if not value.strip():
            raise ValueError("semantic_type must be a non-empty string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        if not value.strip():
            raise ValueError("semantic_role must be a non-empty string")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None")
        self._semantic_content = value

    def _build_animated_lines(self):
        self.animated_lines = VGroup()
        lines = list(self._iter_stream_submobjects())
        count = len(lines)
        if count == 0:
            return

        for index, line in enumerate(lines):
            animated_line = line.copy()
            animated_line.clear_updaters()
            animated_line._asl_base_line = line
            animated_line._asl_phase = 0.0 if count == 1 else self.lag_range * index / count
            animated_line._asl_anim = self._make_line_animation(animated_line)
            animated_line._asl_total_time = 0.0
            animated_line.add_updater(self._line_updater)
            self.animated_lines.add(animated_line)

    def _iter_stream_submobjects(self):
        if isinstance(self.stream_lines, VGroup):
            for submob in self.stream_lines.submobjects:
                yield submob
        else:
            yield self.stream_lines

    def _make_line_animation(self, line):
        anim_config = dict(self.line_anim_config)
        anim_class = anim_config.pop("anim_class", VShowPassingFlash)
        time_width = anim_config.pop("time_width", 0.3)
        run_time = anim_config.pop("run_time", 1.0)
        animation = anim_class(
            line,
            time_width=time_width,
            run_time=run_time,
            rate_func=linear,
            remover=False,
            **anim_config
        )
        animation.begin()
        return animation

    def _line_updater(self, line, dt):
        anim = line._asl_anim
        anim.total_time += dt * self.rate_multiple
        anim.interpolate((anim.total_time + line._asl_phase) % anim.run_time / anim.run_time)

    def update(self, dt=0, recurse=True):
        self.time += dt
        return super().update(dt, recurse=recurse)

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


def KinematicsAnimatedStreamLines(stream_lines, **kwargs):
    return AnimatedStreamLines(
        stream_lines,
        semantic_type="vector_field",
        semantic_role="kinematics_flow",
        semantic_content=kwargs.pop("semantic_content", None),
        **kwargs
    )


def ElectricFieldAnimatedStreamLines(stream_lines, semantic_content="E = kQ/r^2", **kwargs):
    return AnimatedStreamLines(
        stream_lines,
        semantic_type="vector_field",
        semantic_role="electric_field_line",
        semantic_content=semantic_content,
        **kwargs
    )


def VelocityFieldAnimatedStreamLines(stream_lines, semantic_content=None, **kwargs):
    return AnimatedStreamLines(
        stream_lines,
        semantic_type="vector_field",
        semantic_role="velocity_field",
        semantic_content=semantic_content,
        **kwargs
    )