import cadquery as cq
jaw_length = 80
jaw_width = 30
jaw_thickness = 10
taper_length = 20
shell_thickness = 1.5
chamfer_dim = 0.5
hole_diameter = 5
hole_offset = 20
knurl_height = 2
knurl_cols = 4
knurl_rows = 6
knurl_spacing_x = jaw_length / (knurl_cols + 1)
knurl_spacing_z = jaw_thickness / (knurl_rows + 1)
knurl_pad_width = knurl_spacing_x * 0.6
knurl_pad_height = knurl_spacing_z * 0.6
result = (cq.Workplane("XY")
    .polyline([
        (0, 0),
        (jaw_length - taper_length, 0),
        (jaw_length, jaw_width/2),
        (jaw_length - taper_length, jaw_width),
        (0, jaw_width)
    ])
    .close()
    .extrude(jaw_thickness)
    .shell(shell_thickness)
    .faces(">Y").workplane()
    .rect(knurl_pad_width, knurl_pad_height)
    .rarray(knurl_spacing_x, knurl_spacing_z, knurl_cols, knurl_rows, center=True)
    .extrude(knurl_height)
    .faces(">Z").workplane()
    .pushPoints([(-hole_offset, 0), (hole_offset, 0)])
    .hole(hole_diameter)
    .faces(">Z").edges().chamfer(chamfer_dim)
)
