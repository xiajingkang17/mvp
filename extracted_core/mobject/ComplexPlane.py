class ComplexPlane(NumberPlane):

    def number_to_point(self, number) -> Vect3:
        pass

    def n2p(self, number) -> Vect3:
        pass

    def point_to_number(self, point) -> complex:
        pass

    def p2n(self, point) -> complex:
        pass

    def get_unit_size(self) -> float:
        pass

    def get_default_coordinate_values(self, skip_first) -> list[complex]:
        pass

    def add_coordinate_labels(self, numbers, skip_first, font_size) -> Self:
        pass