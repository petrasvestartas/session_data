import cadquery as cq

# Primary dimensions (max 100 units)
frame_outer_width = 80.0
frame_outer_height = 60.0
frame_thickness = 8.0
inner_margin = 10.0
gusset_length = 20.0
gusset_thickness = 6.0
fillet_radius = 0.5
hole_diameter = 6.0
hole_depth = 12.0
mount_hole_dia = 4.0
mount_hole_offset = 8.0

inner_width = frame_outer_width - 2 * inner_margin
inner_height = frame_outer_height - 2 * inner_margin

frame = (
    cq.Workplane("XY")
    .rect(frame_outer_width, frame_outer_height)
    .extrude(frame_thickness)
)
frame = (
    frame.faces(">Z").workplane()
    .rect(inner_width, inner_height)
    .cutBlind(-frame_thickness)
)
frame = frame.edges().fillet(fillet_radius)
tri_prism = (
    cq.Workplane("XY")
    .polyline([
        (0, 0),
        (gusset_length, 0),
        (0, gusset_length)
    ])
    .close()
    .extrude(gusset_thickness)
    .translate((inner_margin, inner_margin, frame_thickness/2))
)
frame = frame.union(tri_prism)
corner_coords = [
    (mount_hole_offset, mount_hole_offset),
    (frame_outer_width - mount_hole_offset, mount_hole_offset),
    (mount_hole_offset, frame_outer_height - mount_hole_offset),
    (frame_outer_width - mount_hole_offset, frame_outer_height - mount_hole_offset)
]
frame = (
    frame.faces(">Z").workplane()
    .pushPoints([
        (x - frame_outer_width/2, y - frame_outer_height/2) for (x, y) in corner_coords
    ])
    .hole(mount_hole_dia)
)
frame = (
    frame.faces(">Z").workplane()
    .center(0, -frame_outer_height/2 + inner_margin/2)
    .hole(hole_diameter, depth=hole_depth)
)
result = frame
