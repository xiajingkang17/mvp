class ApplyMethod(Transform):

    def __init__(self, method):
        """
        method is a method of Mobject, *args are arguments for
        that method.  Key word arguments should be passed in
        as the last arg, as a dict, since **kwargs is for
        configuration of the transform itself
        
        Relies on the fact that mobject methods return the mobject
        """

    def check_validity_of_input(self, method) -> None:
        pass

    def create_target(self) -> Mobject:
        pass