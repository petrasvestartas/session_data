import cadquery as cq
bracket_length = 80.0
bracket_width = 40.0
bracket_thickness = 8.0
reinforcement_cut_width = 20.0
reinforcement_cut_depth = 12.0
hole_diameter = 4.5
hole_spacing = 20.0
hole_count = 3
chamfer_size = 0.5
start_offset = - (hole_spacing * (hole_count - 1)) / 2
result = (
    cq.Workplane("XY")
    .rect(bracket_length, bracket_width)
    .extrude(bracket_thickness)
    .faces(">Z")
    .workplane()
    .center(-bracket_length/2 + reinforcement_cut_width/2, 0)
    .lineTo(reinforcement_cut_width, 0)
    .threePointArc((reinforcement_cut_width/2, reinforcement_cut_depth), (0, reinforcement_cut_depth))
    .close()
    .cutBlind(-reinforcement_cut_depth)
    .faces(">Z")
    .workplane()
    .center(start_offset, 0)
    .rarray(hole_spacing, 0, hole_count, 1)
    .hole(hole_diameter)
    .edges()
    .chamfer(chamfer_size)
)
