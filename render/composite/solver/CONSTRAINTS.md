# Composite Solver Constraints

Current supported constraint types in `render/composite/solver/`:

- `attach` (`attach.py`): make two anchors coincide.
- `midpoint` (`midpoint.py`): place one anchor at midpoint of two references.
- `distance` (`distance.py`): constrain distance between two anchors.
- `on_track_pose` (`on_track_pose.py`): snap part anchor onto track point/tangent with optional offsets.

Notes:

- `attach` supports `mode` and `rigid` (rigid weld group).
- `align_angle` and `align_axis` are removed.
