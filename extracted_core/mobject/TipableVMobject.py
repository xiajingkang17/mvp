class TipableVMobject(VMobject):
    """
    Meant for shared functionality between Arc and Line.
    Functionality can be classified broadly into these groups:
    
        * Adding, Creating, Modifying tips
            - add_tip calls create_tip, before pushing the new tip
                into the TipableVMobject's list of submobjects
            - stylistic and positional configuration
    
        * Checking for tips
            - Boolean checks for whether the TipableVMobject has a tip
                and a starting tip
    
        * Getters
            - Straightforward accessors, returning information pertaining
                to the TipableVMobject instance's tip(s), its length etc
    """

    def add_tip(self, at_start) -> Self:
        """
        Adds a tip to the TipableVMobject instance, recognising
        that the endpoints might need to be switched if it's
        a 'starting tip' or not.
        """

    def create_tip(self, at_start) -> ArrowTip:
        """
        Stylises the tip, positions it spacially, and returns
        the newly instantiated tip to the caller.
        """

    def get_unpositioned_tip(self) -> ArrowTip:
        """
        Returns a tip that has been stylistically configured,
        but has not yet been given a position in space.
        """

    def position_tip(self, tip, at_start) -> ArrowTip:
        pass

    def reset_endpoints_based_on_tip(self, tip, at_start) -> Self:
        pass

    def asign_tip_attr(self, tip, at_start) -> Self:
        pass

    def has_tip(self) -> bool:
        pass

    def has_start_tip(self) -> bool:
        pass

    def pop_tips(self) -> VGroup:
        pass

    def get_tips(self) -> VGroup:
        """
        Returns a VGroup (collection of VMobjects) containing
        the TipableVMObject instance's tips.
        """

    def get_tip(self) -> ArrowTip:
        """
        Returns the TipableVMobject instance's (first) tip,
        otherwise throws an exception.
        """

    def get_default_tip_length(self) -> float:
        pass

    def get_first_handle(self) -> Vect3:
        pass

    def get_last_handle(self) -> Vect3:
        pass

    def get_end(self) -> Vect3:
        pass

    def get_start(self) -> Vect3:
        pass

    def get_length(self) -> float:
        pass