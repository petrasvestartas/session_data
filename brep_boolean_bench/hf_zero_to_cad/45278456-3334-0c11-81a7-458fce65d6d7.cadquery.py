import cadquery as cq

# Parameters
base_side = 30.0
intermediate_ratio = 0.8
intermediate_side = base_side * intermediate_ratio
top_diameter = 30.0
total_height = 80.0
transition_height = 30.0
fillet_radius = 2.0
mount_hole_dia = 5.0
mount_hole_offset = 10.0
rib_thickness = 4.0
rib_width = 12.0
rib_height = 20.0
pocket_width = 6.0
pocket_height = 12.0
pocket_depth = 2.0

# Base lofted column from square to circle with intermediate square
column = (
    cq.Workplane("XY")
    .rect(base_side, base_side)
    .workplane(offset=transition_height)
    .rect(intermediate_side, intermediate_side)
    .workplane(offset=total_height - transition_height)
    .circle(top_diameter / 2)
    .loft(combine=True)
)

# Fillet all edges for safety
column = column.edges().fillet(fillet_radius)

# Mounting holes on the square base (4-hole pattern)
hole_positions = [
    (-base_side/2 + mount_hole_offset, -base_side/2 + mount_hole_offset),
    ( base_side/2 - mount_hole_offset, -base_side/2 + mount_hole_offset),
    (-base_side/2 + mount_hole_offset,  base_side/2 - mount_hole_offset),
    ( base_side/2 - mount_hole_offset,  base_side/2 - mount_hole_offset),
]
column = (
    column.faces("<Z")
    .workplane()
    .pushPoints(hole_positions)
    .hole(mount_hole_dia)
)

# Add a longitudinal rib on the +X side (ensure intersection)
rib = (
    cq.Workplane("YZ")
    .center(0, total_height/2)
    .rect(rib_width, rib_height)
    .extrude(rib_thickness)
    .translate((base_side/2 - rib_thickness, 0, 0))
)
column = column.union(rib)

# Cut a rectangular pocket on the -X side (partial depth, not through)
pocket = (
    cq.Workplane("YZ")
    .center(0, total_height/2)
    .rect(pocket_width, pocket_height)
    .extrude(-pocket_depth)
    .translate((-base_side/2 + pocket_depth/2, 0, 0))
)
column = column.cut(pocket)

result = column