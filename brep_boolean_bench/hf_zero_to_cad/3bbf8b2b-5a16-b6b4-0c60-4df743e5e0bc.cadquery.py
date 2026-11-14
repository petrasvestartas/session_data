import cadquery as cq
BS = cq.selectors.BoxSelector

# Dimensions
plate_length = 100.0
plate_width = 60.0
plate_height = 10.0
cavity_depth = 8.0
main_channel_width = 12.0
branch_channel_width = 8.0
main_channel_length = 80.0
branch_channel_length = 30.0
branch_offset_x = -10.0
fillet_radius = 2.0
wall_thickness = 5.0
hole_diameter = 6.0
mount_hole_diameter = 5.0
mount_hole_offset = 8.0

# Base solid
base = cq.Workplane("XY").box(plate_length, plate_width, plate_height, centered=True)

# Cavity profile sketch on top face
cavity = (
    cq.Workplane("XY", (0, 0, plate_height/2))
    .moveTo(-main_channel_length/2, -main_channel_width/2)
    .lineTo(-main_channel_length/2, main_channel_width/2)
    .lineTo(branch_offset_x, main_channel_width/2)
    .lineTo(branch_offset_x, main_channel_width/2 + branch_channel_width)
    .lineTo(branch_offset_x + branch_channel_length, main_channel_width/2 + branch_channel_width)
    .lineTo(branch_offset_x + branch_channel_length, main_channel_width/2)
    .lineTo(main_channel_length/2, main_channel_width/2)
    .lineTo(main_channel_length/2, -main_channel_width/2)
    .lineTo(branch_offset_x + branch_channel_length, -main_channel_width/2)
    .lineTo(branch_offset_x + branch_channel_length, -(main_channel_width/2 + branch_channel_width))
    .lineTo(branch_offset_x, -(main_channel_width/2 + branch_channel_width))
    .lineTo(branch_offset_x, -main_channel_width/2)
    .lineTo(-main_channel_length/2, -main_channel_width/2)
    .close()
    .extrude(-cavity_depth)
    .fillet(fillet_radius)
)

# Subtract cavity from base
part = base.cut(cavity)

# Add inlet/outlet holes on top face
hole_positions = [
    (-main_channel_length/2 + wall_thickness/2, 0),
    (main_channel_length/2 - wall_thickness/2, 0),
    (branch_offset_x + branch_channel_length - wall_thickness/2, main_channel_width/2 + branch_channel_width/2),
    (branch_offset_x + branch_channel_length - wall_thickness/2, -(main_channel_width/2 + branch_channel_width/2))
]
part = part.faces(">Z").workplane().pushPoints(hole_positions).hole(hole_diameter)

# Add mounting holes at corners
px = plate_length/2 - mount_hole_offset - mount_hole_diameter/2
py = plate_width/2 - mount_hole_offset - mount_hole_diameter/2
part = part.faces("<Z").workplane().pushPoints([
    ( px,  py),
    (-px,  py),
    (-px, -py),
    ( px, -py)
]).hole(mount_hole_diameter)

result = part
