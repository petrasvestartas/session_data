import pathlib
import sys

sys.path.insert(0, r"C:\brg\compas_tf\src")
sys.path.insert(0, r"C:\pc\3_code\code_rust\session\session_py\src")

import compas
from compas_model.elements.group import Group

import compas_tf  # noqa: F401
from compas_tf.plate import PlateElement

try:
    from compas_tf.solid_difference_modifier import SolidDifferenceModifier
    from compas_tf.solid_union_modifier import SolidUnionModifier
    from compas_tf.joint_dowel import DowelElement
    from compas_tf.wedge import WedgeElement
    from compas_tf.joint_hilti import HiltiElement
    from compas_tf.joint_screw import ScrewElement
    from compas_tf.joint_sherpaxl120 import SherpaXL120Element
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
#  Load FloorModel from pre-built JSON
# ------------------------------------------------------------------ #

floor_model = compas.json_load(DATA_JSON)

try:
    contacts = list(floor_model.contacts())
except Exception:
    contacts = []
print(f"[contacts] {len(contacts)} contact(s) found")

# ------------------------------------------------------------------ #
#  Colors
# ------------------------------------------------------------------ #

DEFAULT_COLOR = Color(0.80, 0.80, 0.80, 1.0)


def is_connector(element):
    return bool(CONNECTOR_TYPES) and isinstance(element, CONNECTOR_TYPES)


# ------------------------------------------------------------------ #
#  Build hidden_sources using object identity (matches model.py)
# ------------------------------------------------------------------ #

hidden_sources = set()
if _HAS_MODIFIERS:
    for edge in floor_model.graph.edges():
        modifiers = floor_model.graph.edge_attribute(edge, name="modifiers")
        if not modifiers:
            continue
        for modifier in modifiers:
            u, _v = edge
            src = floor_model.graph.node_element(u)
            if isinstance(modifier, (SolidDifferenceModifier, SolidUnionModifier)):
                hidden_sources.add(src)


def _is_hidden(element):
    if not _HAS_MODIFIERS:
        return False
    if element not in hidden_sources:
        return False
    return not isinstance(element, (DowelElement, WedgeElement))


# ------------------------------------------------------------------ #
#  Build element_connectors using object identity
# ------------------------------------------------------------------ #

element_connectors = {}
for edge in floor_model.graph.edges():
    u, v = edge
    a = floor_model.graph.node_element(u)
    b = floor_model.graph.node_element(v)
    if is_connector(a) and not is_connector(b):
        connector, element = a, b
    elif is_connector(b) and not is_connector(a):
        connector, element = b, a
    else:
        continue
    element_connectors.setdefault(element, [])
    if connector not in element_connectors[element]:
        element_connectors[element].append(connector)

# ------------------------------------------------------------------ #
#  Session builder
# ------------------------------------------------------------------ #

session = Session(name="floor_model")
mesh_count = 0
poly_count = 0
element_to_session_guid = {}  # str(compas element guid) -> session mesh guid


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
    element_to_session_guid[str(element.guid)] = m.guid
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
            session.add(grp, parent_node)
            traverse_element(child, grp)
        else:
            if _is_hidden(child):
                continue
            child_node = add_element_to_session(child, parent_node)
            if child_node is None:
                continue
            connectors = element_connectors.get(child, [])
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
#  Build session tree
# ------------------------------------------------------------------ #

model_node = TreeNode(name="model")
session.add(model_node)

for node in floor_model.tree.root.children:
    element = node.element
    if isinstance(element, Group):
        gname = element.name or "group"
        grp = TreeNode(name=gname)
        session.add(grp, model_node)
        traverse_element(element, grp)
    else:
        if _is_hidden(element):
            continue
        elem_node = add_element_to_session(element, model_node)
        if elem_node is not None:
            connectors = element_connectors.get(element, [])
            if connectors:
                conn_node = TreeNode(name="connectors")
                session.add(conn_node, elem_node)
                for connector in connectors:
                    add_element_to_session(connector, conn_node)

# ------------------------------------------------------------------ #
#  Add contacts as filled meshes
# ------------------------------------------------------------------ #

CONTACT_COLOR = DEFAULT_COLOR
contacts_node = TreeNode(name="contacts")
session.add(contacts_node, model_node)
for i, contact in enumerate(contacts):
    poly = contact.polygon
    pts = [Point(pt[0], pt[1], pt[2]) for pt in poly.points]
    faces = [[0, j, j + 1] for j in range(1, len(pts) - 1)]
    cm = Mesh.from_vertices_and_faces(pts, faces)
    cm.name = f"contact_{i}"
    cm.set_objectcolor(CONTACT_COLOR)
    session.add_mesh(cm, parent=contacts_node)
    mesh_count += 1

# ------------------------------------------------------------------ #
#  Export graph edges
# ------------------------------------------------------------------ #

edge_count = 0
for edge in floor_model.graph.edges():
    u, v = edge
    ga = floor_model.graph.node_element(u)
    gb = floor_model.graph.node_element(v)
    guid_a = element_to_session_guid.get(str(ga.guid))
    guid_b = element_to_session_guid.get(str(gb.guid))
    if not guid_a or not guid_b:
        continue
    if is_connector(ga) and is_connector(gb):
        continue
    attr = "fastener" if (is_connector(ga) or is_connector(gb)) else "contact"
    session.add_edge(guid_a, guid_b, attr)
    edge_count += 1

# ------------------------------------------------------------------ #
#  Save
# ------------------------------------------------------------------ #

session.pb_dump(str(OUTPUT))
print(f"Saved {mesh_count} mesh(es), {poly_count} polyline(s), {len(contacts)} contact(s), {edge_count} graph edge(s) -> {OUTPUT}")
