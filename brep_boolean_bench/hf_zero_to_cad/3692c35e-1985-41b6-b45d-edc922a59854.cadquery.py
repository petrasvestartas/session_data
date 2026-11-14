import cadquery as cq

# Parameters
cap_outer_diameter = 80.0
cap_height = 30.0
cap_wall_thickness = 5.0
pocket_diameter = 30.0
pocket_depth = 10.0
pocket_fillet_radius = 2.0
mount_hole_diameter = 6.0
mount_hole_offset = 20.0
counterbore_diameter = 12.0
counterbore_depth = 5.0
outer_edge_fillet = 1.0
rib_width = 6.0
rib_height = 8.0
rib_length = 15.0
rib_spacing_angle = 60.0
chamfer_size = 0.5

# Base solid cylinder
result = (
    cq.Workplane("XY")
    .circle(cap_outer_diameter / 2)
    .extrude(cap_height)
)

# Thin-walled shell
result = result.shell(-cap_wall_thickness)

# Central blind pocket on interior of top face
result = (
    result
    .faces(">Z")
    .workplane()
    .center(0, 0)
    .circle(pocket_diameter / 2)
    .cutBlind(pocket_depth)
)

# Fillet on pocket bottom edge (horizontal edge)
result = result.edges("not Z").fillet(pocket_fillet_radius)

# Mounting hole with counterbore through top face
result = (
    result
    .faces(">Z")
    .workplane()
    .center(mount_hole_offset, 0)
    .hole(mount_hole_diameter)
    .hole(counterbore_diameter, counterbore_depth)
)

# Fillet on outer top rim (edges furthest in +Z direction)
result = result.edges(">Z").fillet(outer_edge_fillet)

# Add reinforcing ribs on exterior top surface in a circular pattern
num_ribs = int(360 / rib_spacing_angle)
for i in range(num_ribs):
    angle = i * rib_spacing_angle
    rib = (
        cq.Workplane("XY")
        .rect(rib_width, rib_length)
        .extrude(rib_height)
        .translate((cap_outer_diameter / 2 - cap_wall_thickness - rib_width / 2, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), angle)
    )
    result = result.union(rib)

# Small chamfer on the pocket edge where it meets the inner wall
result = result.edges("not Z").chamfer(chamfer_size)
