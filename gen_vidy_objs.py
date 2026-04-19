"""
Generate OBJ files for every wood dataset that has a matching XML in
C:/brg/code_cpp/wood/cmake/src/wood/dataset. Run from session_data:
    cd session_data && python gen_vidy_objs.py
"""
import xml.etree.ElementTree as ET
import os

DATASET_DIR = "C:/brg/code_cpp/wood/cmake/src/wood/dataset"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def xml_to_obj(xml_name, obj_name):
    xml_path = os.path.join(DATASET_DIR, xml_name + ".xml")
    if not os.path.exists(xml_path):
        print(f"skip {obj_name}: {xml_name}.xml not found")
        return
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # Wood mixes capitalized "Polyline" (vidychapel, outofplane, etc.) with
    # lowercase "polyline" (annen_grid_small, vda_floor_*). Accept both.
    polys = root.findall("Polyline") + root.findall("polyline")
    lines = [f"# {xml_name}.xml\n"]
    vi = 1
    for p in polys:
        pts = [
            (float(pt.find("x").text), float(pt.find("y").text), float(pt.find("z").text))
            for pt in p.findall("point")
        ]
        for x, y, z in pts:
            lines.append(f"v {x} {y} {z}\n")
        n = len(pts)
        idxs = " ".join(str(vi + k) for k in range(n))
        parm = "0 " + " ".join(str(k) for k in range(n))
        lines += [
            "cstype bspline\n",
            "deg 1\n",
            f"curv 0 {n} {idxs}\n",
            f"parm u {parm}\n",
            "end\n",
        ]
        vi += n
    with open(os.path.join(OUT_DIR, obj_name), "w") as f:
        f.writelines(lines)
    print(f"wrote {obj_name}: {len(polys)} polylines, {vi-1} vertices")


# (xml_basename, obj_shortname)
DATASETS = [
    # vidychapel family
    ("type_plates_name_joint_linking_vidychapel_corner",           "vidy_corner"),
    ("type_plates_name_joint_linking_vidychapel_one_layer",        "vidy_one_layer"),
    ("type_plates_name_joint_linking_vidychapel_one_axis_two_layers", "vidy_one_axis_two_layers"),
    ("type_plates_name_joint_linking_vidychapel_full",             "vidy_full"),
    # out-of-plane / side-to-side
    ("type_plates_name_side_to_side_edge_outofplane_box",          "outofplane_box"),
    ("type_plates_name_side_to_side_edge_outofplane_tetra",        "outofplane_tetra"),
    ("type_plates_name_side_to_side_edge_outofplane_dodecahedron", "outofplane_dodecahedron"),
    ("type_plates_name_side_to_side_edge_outofplane_icosahedron",  "outofplane_icosahedron"),
    ("type_plates_name_side_to_side_edge_outofplane_octahedron",   "outofplane_octahedron"),
    ("type_plates_name_side_to_side_edge_outofplane_folding",      "vidy_folding"),
    ("type_plates_name_side_to_side_edge_outofplane_inplane_and_top_to_top_hexboxes", "hexboxes"),
    # in-plane
    ("type_plates_name_side_to_side_edge_inplane_2_butterflies",   "inplane_butterflies"),
    ("type_plates_name_side_to_side_edge_inplane_hexshell",        "inplane_hexshell"),
    ("type_plates_name_side_to_side_edge_inplane_differentdirections", "inplane_differentdirections"),
    ("type_plates_name_side_to_side_edge_inplane_hilti",           "inplane_hilti"),
    ("type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners", "simple_corners"),
    ("type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners_combined", "simple_corners_combined"),
    ("type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners_different_lengths", "simple_corners_diff_lengths"),
    # top-to-top / top-to-side
    ("type_plates_name_top_to_top_pairs",                          "top_to_top_pairs"),
    ("type_plates_name_top_to_side_box",                           "top_to_side_box"),
    ("type_plates_name_top_to_side_corners",                       "top_to_side_corners"),
    ("type_plates_name_top_to_side_pairs",                         "top_to_side_pairs"),
    ("type_plates_name_top_to_side_test",                          "top_to_side_test"),
    # annen
    ("type_plates_name_top_to_side_and_side_to_side_outofplane_annen_box",       "annen_box"),
    ("type_plates_name_top_to_side_and_side_to_side_outofplane_annen_box_pair",  "annen_box_pair"),
    ("type_plates_name_top_to_side_and_side_to_side_outofplane_annen_corner",    "annen_corner"),
    ("type_plates_name_top_to_side_and_side_to_side_outofplane_annen_grid_small","annen_grid_small"),
    # cross family
    ("type_plates_name_cross_corners",                             "cross_corners"),
    ("type_plates_name_cross_vda_corner",                          "cross_vda_corner"),
    ("type_plates_name_cross_vda_hexshell",                        "cross_vda_hexshell"),
    ("type_plates_name_cross_vda_hexshell_reciprocal",             "cross_vda_hexshell_reciprocal"),
    ("type_plates_name_cross_vda_shell",                           "cross_vda_shell"),
    ("type_plates_name_cross_vda_single_arch",                     "cross_vda_single_arch"),
    ("type_plates_name_cross_and_sides_corner",                    "cross_and_sides_corner"),
    ("type_plates_name_cross_brg_slab_0",                          "cross_brg_slab_0"),
    ("type_plates_name_cross_brussels_sports_tower",               "cross_brussels_sports_tower"),
    ("type_plates_name_cross_ibois_pavilion",                      "cross_ibois_pavilion"),
    ("type_plates_name_cross_square_reciprocal_iseya",             "cross_square_reciprocal_iseya"),
    ("type_plates_name_cross_square_reciprocal_two_sides",         "cross_square_reciprocal_two_sides"),
    # hex / misc
    ("type_plates_name_hexbox_and_corner",                         "hexbox_and_corner"),
    ("type_plates_name_hex_block_rossiniere",                      "hex_block_rossiniere"),
    # VDA floors
    ("type_plates_name_vda_floor_0",                               "vda_floor_0"),
    ("type_plates_name_vda_floor_1",                               "vda_floor_1"),
    ("type_plates_name_vda_floor_2",                               "vda_floor_2"),
    # beams
    ("type_beams_name_phanomema_node",                             "phanomema_node"),
]

for xml_name, obj_short in DATASETS:
    xml_to_obj(xml_name, obj_short + ".obj")
