================================================================================
Class: TipableVMobject
Source: manimlib/mobject/geometry.py:46
================================================================================

Documentation:
----------------------------------------
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

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: add_tip
    def add_tip(at_start) -> Self

      Adds a tip to the TipableVMobject instance, recognising
      that the endpoints might need to be switched if it's
      a 'starting tip' or not.
    Source line: 71

  Method: create_tip
    def create_tip(at_start) -> ArrowTip

      Stylises the tip, positions it spacially, and returns
      the newly instantiated tip to the caller.
    Source line: 84

  Method: get_unpositioned_tip
    def get_unpositioned_tip() -> ArrowTip

      Returns a tip that has been stylistically configured,
      but has not yet been given a position in space.
    Source line: 93

  Method: position_tip
    def position_tip(tip, at_start) -> ArrowTip
    Source line: 103

  Method: reset_endpoints_based_on_tip
    def reset_endpoints_based_on_tip(tip, at_start) -> Self
    Source line: 116

  Method: asign_tip_attr
    def asign_tip_attr(tip, at_start) -> Self
    Source line: 131

  Method: has_tip
    def has_tip() -> bool
    Source line: 139

  Method: has_start_tip
    def has_start_tip() -> bool
    Source line: 142

  Method: pop_tips
    def pop_tips() -> VGroup
    Source line: 146

  Method: get_tips
    def get_tips() -> VGroup

      Returns a VGroup (collection of VMobjects) containing
      the TipableVMObject instance's tips.
    Source line: 158

  Method: get_tip
    def get_tip() -> ArrowTip

      Returns the TipableVMobject instance's (first) tip,
      otherwise throws an exception.
    Source line: 170

  Method: get_default_tip_length
    def get_default_tip_length() -> float
    Source line: 179

  Method: get_first_handle
    def get_first_handle() -> Vect3
    Source line: 182

  Method: get_last_handle
    def get_last_handle() -> Vect3
    Source line: 185

  Method: get_end
    def get_end() -> Vect3
    Source line: 188

  Method: get_start
    def get_start() -> Vect3
    Source line: 194

  Method: get_length
    def get_length() -> float
    Source line: 200
