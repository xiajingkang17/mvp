from manimlib import *
import numpy as np


class Line(TipableVMobject):
    CONFIG = {
        "buff": 0.0,
        "path_arc": 0.0,
        "n_points_per_curve": 20,
        "semantic_type": "geometric_shape",
        "semantic_role": "line_segment",
        "semantic_content": None,
    }

    def __init__(self, start=LEFT, end=RIGHT, buff=0.0, path_arc=0.0, **kwargs):
        semantic_type = kwargs.pop("semantic_type", self.CONFIG["semantic_type"])
        semantic_role = kwargs.pop("semantic_role", self.CONFIG["semantic_role"])
        semantic_content = kwargs.pop("semantic_content", self.CONFIG["semantic_content"])
        super().__init__(buff=buff, path_arc=path_arc, **kwargs)
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content
        self.set_start_and_end_attrs(start, end)
        self.set_points_by_ends(start, end, buff=self.buff, path_arc=self.path_arc)

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

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj

    def set_points_by_ends(self, start, end, buff=0.0, path_arc=0.0):
        self.set_start_and_end_attrs(start, end)
        start_point = np.array(self.start)
        end_point = np.array(self.end)
        vect = end_point - start_point
        dist = get_norm(vect)

        if dist == 0:
            self.set_points_as_corners([start_point, end_point])
            return self

        buff = max(0.0, float(buff))
        if 2 * buff >= dist:
            midpoint = midpoint(start_point, end_point)
            self.set_points_as_corners([midpoint, midpoint])
            return self

        unit_vect = normalize(vect)
        start_point = start_point + buff * unit_vect
        end_point = end_point - buff * unit_vect

        if abs(path_arc) < 1e-8:
            self.set_points_as_corners([start_point, end_point])
        else:
            arc = ArcBetweenPoints(start_point, end_point, angle=path_arc)
            self.set_points(arc.get_points())
        self.account_for_buff()
        return self

    def reset_points_around_ends(self):
        return self.set_points_by_ends(
            self.start,
            self.end,
            buff=self.buff,
            path_arc=self.path_arc,
        )

    def set_path_arc(self, path_arc):
        self.path_arc = path_arc
        return self.reset_points_around_ends()

    def set_start_and_end_attrs(self, start, end):
        rough_start = self.pointify(start, RIGHT)
        rough_end = self.pointify(end, LEFT)

        if np.allclose(rough_start, rough_end):
            self.start = rough_start
            self.end = rough_end
            return self

        vect = normalize(rough_end - rough_start)
        self.start = self.pointify(start, vect)
        self.end = self.pointify(end, -vect)
        return self

    def pointify(self, mob_or_point, direction=None):
        if isinstance(mob_or_point, Mobject):
            if direction is None:
                return np.array(mob_or_point.get_center())
            return np.array(mob_or_point.get_boundary_point(direction))
        return np.array(mob_or_point, dtype=float)

    def put_start_and_end_on(self, start, end):
        self.set_start_and_end_attrs(start, end)
        self.set_points_by_ends(self.start, self.end, buff=self.buff, path_arc=self.path_arc)
        return self

    def get_vector(self):
        return self.get_end() - self.get_start()

    def get_unit_vector(self):
        return normalize(self.get_vector())

    def get_angle(self):
        return angle_of_vector(self.get_vector())

    def get_projection(self, point):
        start = self.get_start()
        vector = self.get_vector()
        norm = np.dot(vector, vector)
        if norm == 0:
            return np.array(start)
        t = np.dot(np.array(point) - start, vector) / norm
        return start + t * vector

    def get_slope(self):
        vector = self.get_vector()
        if abs(vector[0]) < 1e-8:
            return np.inf
        return vector[1] / vector[0]

    def set_angle(self, angle, about_point=None):
        if about_point is None:
            about_point = self.get_start()
        self.rotate(angle - self.get_angle(), about_point=about_point)
        return self

    def set_length(self, length):
        current_length = self.get_length()
        if current_length == 0:
            return self
        self.scale(length / current_length, about_point=self.get_start())
        return self

    def get_arc_length(self):
        return self.get_length()

    def set_perpendicular_to_camera(self, camera_frame):
        start = self.get_start()
        end = self.get_end()
        center = midpoint(start, end)
        length = get_norm(end - start)
        normal = camera_frame.get_implied_camera_location() - center
        normal_norm = get_norm(normal)
        if normal_norm == 0:
            return self

        normal = normal / normal_norm
        reference = OUT
        if abs(np.dot(normal, reference)) > 0.9:
            reference = UP

        direction = normalize(np.cross(normal, reference))
        if get_norm(direction) == 0:
            return self

        new_start = center - 0.5 * length * direction
        new_end = center + 0.5 * length * direction
        return self.put_start_and_end_on(new_start, new_end)

    def get_bbox(self):
        return np.array(self.get_bounding_box())


def KinematicsLine(start=LEFT, end=RIGHT, semantic_content=None, **kwargs):
    return Line(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="kinematics_curve",
        semantic_content=semantic_content,
        **kwargs
    )


def ForceLine(start=LEFT, end=RIGHT, semantic_content=None, **kwargs):
    return Line(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="gravitational_force",
        semantic_content=semantic_content,
        **kwargs
    )


def AxisLine(start=LEFT, end=RIGHT, semantic_content=None, **kwargs):
    return Line(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="x_axis",
        semantic_content=semantic_content,
        **kwargs
    )