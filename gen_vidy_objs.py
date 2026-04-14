"""
Generate OBJ files for vidy chapel datasets from wood XML sources.
Run once: cd session_data && python gen_vidy_objs.py
"""
import xml.etree.ElementTree as ET
import os

DATASET_DIR = "C:/brg/code_cpp/wood/cmake/src/wood/dataset"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def xml_to_obj(xml_name, obj_name):
    tree = ET.parse(os.path.join(DATASET_DIR, xml_name + ".xml"))
    polys = tree.getroot().findall("Polyline")
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
    out_path = os.path.join(OUT_DIR, obj_name)
    with open(out_path, "w") as f:
        f.writelines(lines)
    print(f"wrote {obj_name}: {len(polys)} polylines, {vi-1} vertices")


xml_to_obj(
    "type_plates_name_joint_linking_vidychapel_one_layer",
    "vidy_one_layer.obj",
)
xml_to_obj(
    "type_plates_name_joint_linking_vidychapel_one_axis_two_layers",
    "vidy_one_axis_two_layers.obj",
)
xml_to_obj(
    "type_plates_name_joint_linking_vidychapel_full",
    "vidy_full.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_outofplane_tetra",
    "outofplane_tetra.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_outofplane_dodecahedron",
    "outofplane_dodecahedron.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_outofplane_icosahedron",
    "outofplane_icosahedron.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_outofplane_octahedron",
    "outofplane_octahedron.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners",
    "simple_corners.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners_combined",
    "simple_corners_combined.obj",
)
xml_to_obj(
    "type_plates_name_side_to_side_edge_inplane_outofplane_simple_corners_different_lengths",
    "simple_corners_diff_lengths.obj",
)
xml_to_obj(
    "type_plates_name_top_to_top_pairs",
    "top_to_top_pairs.obj",
)
