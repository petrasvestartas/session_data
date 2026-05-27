import pathlib
import sys

sys.path.insert(0, r"C:\brg\compas_tf\src")
sys.path.insert(0, r"C:\pc\3_code\code_rust\session\session_py\src")

import math

from compas.geometry import Point as CPoint
from compas.geometry import Rotation
from compas.geometry import Translation
from compas.geometry import Vector
from compas_model.elements.group import Group

import compas_tf  # noqa: F401
from compas_tf.floor_builder import FloorBuilder
from compas_tf.floor_guide import FloorGuide
from compas_tf.floor_model import FloorModel
from compas_tf.plate import PlateElement

try:
    from compas_tf.solid_difference_modifier import SolidDifferenceModifier
    from compas_tf.solid_union_modifier import SolidUnionModifier
    from compas_tf.joint_dowel import DowelElement
    from compas_tf.wedge import WedgeElement
    from compas_tf.joint_sherpaxl120 import SherpaXL120Element
    from compas_tf.joint_hilti import HiltiElement
    from compas_tf.joint_screw import ScrewElement
    from compas_tf.joint_strip import AlignmentStripElement
    CONNECTOR_TYPES = (ScrewElement, DowelElement, AlignmentStripElement, SherpaXL120Element, HiltiElement)
    _HAS_MODIFIERS = True
except ImportError:
    CONNECTOR_TYPES = ()
    DowelElement = None
    WedgeElement = None
    HiltiElement = None
    _HAS_MODIFIERS = False

from session_py import Color
from session_py import Mesh
from session_py import Point
from session_py import Polyline
from session_py import Session
from session_py import TreeNode

OUTPUT = pathlib.Path(__file__).parent / "floor_model.pb"
DATA_JSON = pathlib.Path(r"C:\brg\compas_tf\data\floor_model_booleans.json")

# ------------------------------------------------------------------ #
#  Load or build FloorModel
# ------------------------------------------------------------------ #

column_size = 220
builder = FloorBuilder(
    size=3000,
    height=650,
    rise=453,
    oculus=1000,
    beam_w=40,
    column_head_offset=50,
    inner_thick=60,
    outer_thick=100,
    column_head_scale=250,
    column_head_inclination=0,
    head_h=500,
    head_b=100,
    head_o=141,
)
guide = FloorGuide(
    size_grid_x=3000,
    size_grid_y=3000,
    size_column_head=220,
    size_column_head_chamfer=120,
    size_outer_ribs=100,
    size_inner_ribs=60,
    size_inner_beams=60,
    height=650,
    rise=453,
    size_oculus=1000,
    size_wedge=120,
)
floor_model = FloorModel(builder=builder)
floor_model.add_support(column_size=column_size)
floor_model.add_column(column_size=column_size)
floor_level = Translation.from_vector(Vector(0, 0, floor_model.story_height))
floor_model.add_floor_guide(guide, column_index=0, transformation=floor_level, include_oculus=True)
for i in range(1, 4):
    rot = Rotation.from_axis_and_angle(Vector(0, 0, 1), i * math.pi / 2, CPoint(0, 0, 0))
    floor_model.add_floor_guide(guide, column_index=i, transformation=floor_level * rot, include_oculus=False)
floor_model.precompute_boolean_modifiers()
floor_model.compute_contacts_inner_beams(tolerance=1.0, minimum_area=1.0)
contacts = list(floor_model.contacts())
print(f"[contacts] {len(contacts)} contact(s) found")

# ------------------------------------------------------------------ #
#  Colors — matching model.py exactly
# ------------------------------------------------------------------ #

DEFAULT_COLOR = Color(0.80, 0.80, 0.80, 1.0)


def is_connector(element):
    return bool(CONNECTOR_TYPES) and isinstance(element, CONNECTOR_TYPES)


# ------------------------------------------------------------------ #
#  Build guid -> tree element map — tree objects have correct transforms
# ------------------------------------------------------------------ #

guid_to_element = {}

def _collect_tree_elements(element):
    if isinstance(element, Group):
        for child in element.children:
            _collect_tree_elements(child)
    else:
        g = getattr(element, "guid", None)
        if g is not None:
            guid_to_element[str(g)] = element

for _node in floor_model.tree.root.children:
    _collect_tree_elements(_node.element)

# ------------------------------------------------------------------ #
#  Build hidden_guids — same logic as model.py
# ------------------------------------------------------------------ #

hidden_guids = set()
if _HAS_MODIFIERS:
    for edge in floor_model.graph.edges():
        modifiers = floor_model.graph.edge_attribute(edge, name="modifiers")
        if not modifiers:
            continue
        for modifier in modifiers:
            if isinstance(modifier, (SolidDifferenceModifier, SolidUnionModifier)):
                u, _v = edge
                src = floor_model.graph.node_element(u)
                if not isinstance(src, (DowelElement, WedgeElement)):
                    hidden_guids.add(str(src.guid))

# ------------------------------------------------------------------ #
#  Build element_connectors — use tree objects for correct positions
# ------------------------------------------------------------------ #

element_connectors = {}  # element_guid -> [connector, ...]
for edge in floor_model.graph.edges():
    u, v = edge
    ga = floor_model.graph.node_element(u)
    gb = floor_model.graph.node_element(v)
    # Resolve to tree objects (which have correct transformations)
    a = guid_to_element.get(str(ga.guid), ga)
    b = guid_to_element.get(str(gb.guid), gb)
    if is_connector(a) and not is_connector(b):
        connector, element = a, b
    elif is_connector(b) and not is_connector(a):
        connector, element = b, a
    else:
        continue
    eg = str(element.guid)
    element_connectors.setdefault(eg, [])
    if str(connector.guid) not in [str(c.guid) for c in element_connectors[eg]]:
        element_connectors[eg].append(connector)

# ------------------------------------------------------------------ #
#  Session builder — mirrors add_model_to_viewer from model.py
# ------------------------------------------------------------------ #

PROMOTE = set()

session = Session(name="floor_model")
mesh_count = 0
poly_count = 0


def add_element_to_session(element, parent_node):
    global mesh_count, poly_count
    compas_mesh = getattr(element, "modelgeometry", None)
    if compas_mesh is None:
        return None
    name = getattr(element, "name", None) or "element"
    plate = TreeNode(name=name)
    session.add(plate, parent_node)
    vertices_coords, faces = compas_mesh.to_vertices_and_faces()
    pts = [Point(x, y, z) for x, y, z in vertices_coords]
    m = Mesh.from_vertices_and_faces(pts, faces)
    m.name = name
    m.set_objectcolor(DEFAULT_COLOR)
    session.add_mesh(m, parent=plate)
    mesh_count += 1
    if isinstance(element, PlateElement):
        top = getattr(element, "top_polyline", None)
        bot = getattr(element, "bottom_polyline", None)
        if top is not None or bot is not None:
            pl_node = TreeNode(name="polylines")
            session.add(pl_node, plate)
            if top is not None:
                pts = [Point(pt[0], pt[1], pt[2]) for pt in top.points]
                pl = Polyline(pts)
                pl.name = name + "_top"
                session.add_polyline(pl, parent=pl_node)
                poly_count += 1
            if bot is not None:
                pts = [Point(pt[0], pt[1], pt[2]) for pt in bot.points]
                pl = Polyline(pts)
                pl.name = name + "_bot"
                session.add_polyline(pl, parent=pl_node)
                poly_count += 1
    return plate


def traverse_element(element, parent_node):
    for child in element.children:
        if isinstance(child, Group):
            cname = child.name or "group"
            grp = TreeNode(name=cname)
            if cname in PROMOTE:
                session.add(grp)
            else:
                session.add(grp, parent_node)
            traverse_element(child, grp)
        else:
            if str(child.guid) in hidden_guids:
                continue
            child_node = add_element_to_session(child, parent_node)
            if child_node is None:
                continue
            connectors = element_connectors.get(str(child.guid), [])
            if connectors:
                conn_node = TreeNode(name="connectors")
                session.add(conn_node, child_node)
                for connector in connectors:
                    if _HAS_MODIFIERS and isinstance(connector, (HiltiElement, DowelElement)):
                        continue
                    add_element_to_session(connector, conn_node)
            for grandchild in child.children:
                if isinstance(grandchild, Group):
                    traverse_element(grandchild, child_node)


# ------------------------------------------------------------------ #
#  Build session tree — same traversal order as add_model_to_viewer
# ------------------------------------------------------------------ #

model_node = TreeNode(name="model")
session.add(model_node)

for node in floor_model.tree.root.children:
    element = node.element
    if isinstance(element, Group):
        gname = element.name or "group"
        grp = TreeNode(name=gname)
        if gname in PROMOTE:
            session.add(grp)
        else:
            session.add(grp, model_node)
        traverse_element(element, grp)
    else:
        if str(element.guid) in hidden_guids:
            continue
        elem_node = add_element_to_session(element, model_node)
        if elem_node is not None:
            connectors = element_connectors.get(str(element.guid), [])
            if connectors:
                conn_node = TreeNode(name="connectors")
                session.add(conn_node, elem_node)
                for connector in connectors:
                    add_element_to_session(connector, conn_node)

# ------------------------------------------------------------------ #
#  Add contacts as red filled meshes + outline polylines
# ------------------------------------------------------------------ #

CONTACT_COLOR = DEFAULT_COLOR
contacts_node = TreeNode(name="contacts")
session.add(contacts_node, model_node)
for i, contact in enumerate(contacts):
    poly = contact.polygon
    pts = [Point(pt[0], pt[1], pt[2]) for pt in poly.points]
    # Fan-triangulate the contact polygon into a mesh
    faces = [[0, j, j + 1] for j in range(1, len(pts) - 1)]
    cm = Mesh.from_vertices_and_faces(pts, faces)
    cm.name = f"contact_{i}"
    cm.set_objectcolor(CONTACT_COLOR)
    session.add_mesh(cm, parent=contacts_node)
    mesh_count += 1

# ------------------------------------------------------------------ #
#  Save
# ------------------------------------------------------------------ #

session.pb_dump(str(OUTPUT))
print(f"Saved {mesh_count} mesh(es), {poly_count} polyline(s), {len(contacts)} contact(s) -> {OUTPUT}")
