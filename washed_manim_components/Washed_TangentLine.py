from manimlib import *


class TangentLine(Line):
    CONFIG = {
        "d_alpha": 1e-6,
        "length": 4.0,
        "semantic_type": "geometric_shape",
        "semantic_role": "tangent_line",
        "semantic_content": None,
    }

    def __init__(
        self,
        vmob,
        alpha,
        length=None,
        d_alpha=None,
        semantic_type=None,
        semantic_role=None,
        semantic_content=None,
        **kwargs
    ):
        self.vmob = vmob
        self.alpha = float(alpha)

        if d_alpha is None:
            d_alpha = self.CONFIG["d_alpha"]
        self.d_alpha = float(d_alpha)

        if length is None:
            length = self.CONFIG["length"]
        self.length = float(length)

        a1, a2 = self._get_clamped_alpha_pair(self.alpha, self.d_alpha)
        p1 = vmob.point_from_proportion(a1)
        p2 = vmob.point_from_proportion(a2)

        if get_norm(p2 - p1) == 0:
            p1, p2 = self._get_fallback_points(vmob, self.alpha)

        super().__init__(p1, p2, **kwargs)
        self.set_width(self.length)

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None

        self.semantic_type = semantic_type if semantic_type is not None else self.CONFIG["semantic_type"]
        self.semantic_role = semantic_role if semantic_role is not None else self.CONFIG["semantic_role"]
        self.semantic_content = (
            semantic_content
            if semantic_content is not None
            else self._default_semantic_content()
        )

    def _get_clamped_alpha_pair(self, alpha, d_alpha):
        half_step = 0.5 * abs(d_alpha)
        a1 = np.clip(alpha - half_step, 0.0, 1.0)
        a2 = np.clip(alpha + half_step, 0.0, 1.0)

        if a1 == a2:
            if alpha <= 0.5:
                a2 = np.clip(alpha + max(abs(d_alpha), 1e-4), 0.0, 1.0)
            else:
                a1 = np.clip(alpha - max(abs(d_alpha), 1e-4), 0.0, 1.0)
        return a1, a2

    def _get_fallback_points(self, vmob, alpha):
        eps = 1e-4
        a1 = np.clip(alpha - eps, 0.0, 1.0)
        a2 = np.clip(alpha + eps, 0.0, 1.0)
        return vmob.point_from_proportion(a1), vmob.point_from_proportion(a2)

    def _default_semantic_content(self):
        return "alpha={:.6f}".format(self.alpha)

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

    def set_semantic_labels(self, semantic_type=None, semantic_role=None, semantic_content=None):
        if semantic_type is not None:
            self.semantic_type = semantic_type
        if semantic_role is not None:
            self.semantic_role = semantic_role
        if semantic_content is not None or semantic_content is None:
            self.semantic_content = semantic_content
        return self

    def get_bbox(self):
        return np.array(self.get_bounding_box())

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        new_obj.vmob = getattr(self, "vmob", None)
        new_obj.alpha = getattr(self, "alpha", 0.0)
        new_obj.d_alpha = getattr(self, "d_alpha", self.CONFIG["d_alpha"])
        new_obj.length = getattr(self, "length", self.CONFIG["length"])
        return new_obj


def CircleTangentLine(circle, alpha, length=4.0, d_alpha=1e-6, **kwargs):
    return TangentLine(
        circle,
        alpha=alpha,
        length=length,
        d_alpha=d_alpha,
        semantic_type="geometric_shape",
        semantic_role="circle_tangent",
        semantic_content="circle alpha={:.6f}".format(float(alpha)),
        **kwargs
    )


def FunctionTangentLine(curve, alpha, length=4.0, d_alpha=1e-6, **kwargs):
    return TangentLine(
        curve,
        alpha=alpha,
        length=length,
        d_alpha=d_alpha,
        semantic_type="function_curve",
        semantic_role="function_tangent",
        semantic_content="curve alpha={:.6f}".format(float(alpha)),
        **kwargs
    )


def KinematicsTangentLine(curve, alpha, length=4.0, d_alpha=1e-6, **kwargs):
    return TangentLine(
        curve,
        alpha=alpha,
        length=length,
        d_alpha=d_alpha,
        semantic_type="function_curve",
        semantic_role="kinematics_tangent",
        semantic_content="velocity_or_slope alpha={:.6f}".format(float(alpha)),
        **kwargs
    )