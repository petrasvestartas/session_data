import cadquery as cq
from types import SimpleNamespace as Measures
import math

m = Measures(
    outer_diameter = 80.0,
    block_width = 45.0,
    block_depth = 20.0,
    block_height = 15.0,
    wall_thickness = 3.0,
    outer_fillet_radius = 1.0,
    countersink_diameter = 8.0,
    countersink_angle = 82,
    countersink_hole_diameter = 4.0,
    mount_hole_spacing = 30.0,
    mount_hole_diameter = 4.5,
    mount_hole_offset_y = 5.0
)

m.outer_radius = 0.5 * m.outer_diameter
m.arc_center_angle = math.degrees(math.acos((2 * m.outer_radius**2 - m.block_width**2) / (2 * m.outer_radius**2)))
m.arc_secant_angle = 0.5 * (180.0 - m.arc_center_angle)

path = (
    cq.Workplane("XY")
    .radiusArc((m.block_width, 0.0), m.outer_radius)
    .wire()
)

swept = (
    cq.Workplane("XY")
    .transformed(rotate=(90, -m.arc_secant_angle, 0))
    .rect(m.block_depth, m.block_height)
    .sweep(path, transition="round")
    .edges()
    .fillet(m.outer_fillet_radius)
)

hollow = swept.shell(-m.wall_thickness)

with_holes = (
    hollow
    .faces(">Z")
    .workplane()
    .pushPoints([
        (-m.mount_hole_spacing/2, m.mount_hole_offset_y),
        ( m.mount_hole_spacing/2, m.mount_hole_offset_y)
    ])
    .hole(m.mount_hole_diameter)
)

result = (
    with_holes
    .faces(">Z")
    .workplane()
    .cskHole(m.countersink_hole_diameter, m.countersink_diameter, m.countersink_angle)
)
