# Rebuilds of McNeel forum boolean failures as STEP parts (own geometry, written with OCCT 8.0.1 via cadquery-ocp).
#   gen_forum.py <outdir>
# threaded_rod_cutter.step : triangular thread profile swept along a helix (t/216730 "Threads and Solid Booleans")
# mesh_blob_80.step         : a closed solid of 80 planar triangles from a perturbed icosphere (t/123416, polysurfaces made from meshes)
import sys, math, os
from OCP.gp import gp_Pnt, gp_Ax2, gp_Ax3, gp_Dir, gp_Pnt2d, gp_Dir2d, gp_Lin2d
from OCP.Geom import Geom_CylindricalSurface
from OCP.Geom2d import Geom2d_Line
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakePolygon,
                                BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid)
from OCP.BRepLib import BRepLib
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopoDS import TopoDS
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.ShapeFix import ShapeFix_Solid

out = sys.argv[1]
os.makedirs(out, exist_ok=True)


def write(shape, name):
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, g)
    w = STEPControl_Writer()
    w.Transfer(shape, STEPControl_AsIs)
    w.Write(os.path.join(out, name))
    print(name, 'valid', BRepCheck_Analyzer(shape).IsValid(), 'volume', g.Mass())


# Thread cutter: helix radius r on a cylinder, pitch p, n turns; triangle profile in the XZ plane at the helix start.
r, p, n = 5.0, 2.0, 5
cyl = Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), r)
line = Geom2d_Line(gp_Pnt2d(0, 0), gp_Dir2d(2 * math.pi, p))
helix = BRepBuilderAPI_MakeEdge(line, cyl, 0.0, n * math.hypot(2 * math.pi, p)).Edge()
BRepLib.BuildCurves3d_s(helix)
spine = BRepBuilderAPI_MakeWire(helix).Wire()
d = 0.8  # profile depth into the rod and half height
prof = BRepBuilderAPI_MakePolygon(gp_Pnt(r - d, 0, 0), gp_Pnt(r + 0.6, 0, -0.75), gp_Pnt(r + 0.6, 0, 0.75), True).Wire()
pipe = BRepOffsetAPI_MakePipeShell(spine)
pipe.SetMode(gp_Dir(0, 0, 1))
pipe.Add(prof)
pipe.Build()
pipe.MakeSolid()
write(pipe.Shape(), 'threaded_rod_cutter.step')

# Perturbed icosphere, subdivided once: 80 planar triangles sewn into a solid.
t = (1 + 5 ** 0.5) / 2
V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
     (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
V = [tuple(c / math.sqrt(sum(x * x for x in v)) for c in v) for v in V]
mid = {}


def midpoint(a, b):
    k = (min(a, b), max(a, b))
    if k not in mid:
        m = [(V[a][i] + V[b][i]) / 2 for i in range(3)]
        l = math.sqrt(sum(x * x for x in m))
        V.append(tuple(x / l for x in m))
        mid[k] = len(V) - 1
    return mid[k]


F2 = []
for a, b, c in F:
    ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
    F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
R = [20.0 * (1 + 0.12 * math.sin(3 * v[0] + 2 * v[1]) + 0.08 * math.cos(4 * v[2])) for v in V]
P = [gp_Pnt(*(R[i] * c for c in V[i])) for i in range(len(V))]
sew = BRepBuilderAPI_Sewing(1e-6)
for a, b, c in F2:
    w = BRepBuilderAPI_MakePolygon(P[a], P[b], P[c], True).Wire()
    sew.Add(BRepBuilderAPI_MakeFace(w, True).Face())
sew.Perform()
shell = TopoDS.Shell(sew.SewedShape())
solid = BRepBuilderAPI_MakeSolid(shell).Solid()
fix = ShapeFix_Solid(solid)
fix.Perform()
write(fix.Solid(), 'mesh_blob_80.step')
