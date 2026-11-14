import cadquery as cq

# Parameters
height_total = 80.0
large_diameter = 40.0
small_diameter = 20.0
counterbore_diameter = 30.0
counterbore_depth = 10.0
rib_height = 5.0
rib_width = 6.0
wall_thickness = 2.0
chamfer_length = 1.0
mount_hole_diameter = 3.0
mount_hole_count = 4
mount_hole_radius = large_diameter / 2 - 5.0
polar_angle = 360.0 / mount_hole_count

# Build 2D profile on YZ plane and revolve
profile = (
    cq.Workplane("YZ")
    .moveTo(0, 0)
    .lineTo(large_diameter / 2, 0)
    .lineTo(large_diameter / 2, counterbore_depth)
    .lineTo(counterbore_diameter / 2, counterbore_depth)
    .lineTo(counterbore_diameter / 2, counterbore_depth + rib_height)
    .lineTo(large_diameter / 2 + rib_width, counterbore_depth + rib_height)
    .lineTo(small_diameter / 2, height_total)
    .lineTo(0, height_total)
    .close()
)

solid = profile.revolve()
chammed_solid = solid.edges().chamfer(chamfer_length)
shelled = chammed_solid.shell(wall_thickness)

result = (
    shelled
    .faces("<Y")
    .first()
    .workplane()
    .polarArray(radius=mount_hole_radius, startAngle=0, angle=polar_angle, count=mount_hole_count)
    .hole(mount_hole_diameter)
)
