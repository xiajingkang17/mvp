class ShowPartial(Animation, ABC):
    """
    Abstract class for ShowCreation and ShowPassingFlash
    """

    def __init__(self, mobject, should_match_start):
        pass

    def interpolate_submobject(self, submob, start_submob, alpha) -> None:
        pass

    @abstractmethod
    def get_bounds(self, alpha) -> tuple[float, float]:
        pass