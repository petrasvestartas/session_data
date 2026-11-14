import cadquery as cq
from math import acos, degrees
from types import SimpleNamespace as Measures

m = Measures(
    block_width = 60.0,
    block_depth = 20.0,
    block_height = 15.0,
    arc_radius = 50.0,
    boss_radius = 8.0,
    boss_height = 5.0,
    tap_diameter = 5.0,
    rib_count = 8,
    rib_width = 5.0,
    rib_thickness = 2.0,
    rib_height = 3.0,
    rib_offset = 10.0,
    chamfer = 0.5,
    vertical_fillet = 1.0,
    top_fillet = 1.0,
)

m.arc_center_angle = degrees(2 * acos(m.block_width / (2 * m.arc_radius)))
m.arc_secant_angle = 0.5 * (180.0 - m.arc_center_angle)

path = (
    cq.Workplane("XY")
    .radiusArc((m.block_width, 0.0), m.arc_radius)
    .wire()
)

base = (
    cq.Workplane("XY")
    .transformed(rotate=(90, -m.arc_secant_angle, 0))
    .rect(m.block_depth, m.block_height)
    .sweep(path, transition="round")
    .edges("|Z")
    .fillet(m.vertical_fillet)
    .edges(">Z")
    .fillet(m.top_fillet)
    .edges("<<Z")
    .chamfer(m.chamfer)
)

boss = (
    base.faces(">Z").workplane()
    .center(0, 0)
    .circle(m.boss_radius)
    .extrude(m.boss_height)
)

boss_hole = (
    boss.faces(">Z").workplane()
    .hole(m.tap_diameter)
)

rib_center_radius = (m.block_width / 2.0) - m.rib_offset
rib_profile = (
    cq.Workplane("XY")
    .center(rib_center_radius, 0)
    .rect(m.rib_width, m.rib_thickness)
)

ribs = (
    rib_profile
    .polarArray(count=m.rib_count, radius=rib_center_radius, angle=360, startAngle=0)
    .extrude(m.rib_height)
)

result = base.union(boss_hole).union(ribs)
