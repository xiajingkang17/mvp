from manimlib import *

class Square(Rectangle):
    def __init__(self, side_length=2.0, **kwargs):
        super().__init__(width=side_length, height=side_length, **kwargs)
        self.semantic_type = "geometric_shape"
        self.semantic_role = "geometric_shape"
        self.semantic_content = f"square(side_length={side_length})"

    def copy(self):
        new_obj = super().copy()
        new_obj.semantic_type = getattr(self, 'semantic_type', "geometric_shape")
        new_obj.semantic_role = getattr(self, 'semantic_role', "geometric_shape")
        new_obj.semantic_content = getattr(self, 'semantic_content', "")
        return new_obj