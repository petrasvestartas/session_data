# OCCT side of the STEP boolean bench (brep_boolean_bench/RESULTS.md), through the cadquery-ocp wheel (OCCT 8.0.1).
#   occt_step_bench.py load <file.step>
#     LOAD <file> <status> read_s <s> solids <n> shells <n> [error]
#     SOLID <file> <i> faces edges vertices valid kinds=plane,sphere,cylinder,cone,torus,free(bspline/bezier/revolution/extrusion/offset/other) vol_s volume
#   occt_step_bench.py bool <specA> <specB> [dumpprefix]
#     BOOL <op> <status> bool_s faces edges vertices valid solids vol_s volume [message]   for the five operations
# Specs as in ours_step_bench.cpp: step=<path> picks the solid of largest volume.
import sys, time, math, json
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_REVERSED
from OCP.collections import IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher as TopTools_IndexedMapOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Sphere, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Torus
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone, BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeSphere
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec, gp_Ax1, gp_Dir
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


def count(s, t):
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(s, t, m)
    return m.Extent()


def items(s, t):
    out = []
    e = TopExp_Explorer(s, t)
    while e.More():
        out.append(e.Current())
        e.Next()
    return out


def volume(s):
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    return g.Mass()


def file_unit_mm(path):
    # OCCT converts lengths to millimetres on read; session_cpp keeps file units. Scale OCCT back to file units.
    import re
    t = open(path, errors='replace').read().upper()
    m = re.search(r"CONVERSION_BASED_UNIT\s*\(\s*'(INCH|FOOT|IN|FT)'", t)
    if m:
        return 25.4 if m.group(1) in ('INCH', 'IN') else 304.8
    m = re.search(r"LENGTH_UNIT\s*\(\s*\)\s*NAMED_UNIT\s*\(\s*\*\s*\)\s*SI_UNIT\s*\(\s*([.A-Z$]+)\s*,\s*\.METRE\.", t)
    if not m:
        m = re.search(r"SI_UNIT\s*\(\s*([.A-Z$]+)\s*,\s*\.METRE\.", t)
    if m:
        return {'.MILLI.': 1.0, '.CENTI.': 10.0, '.DECI.': 100.0, '$': 1000.0, '.KILO.': 1e6, '.MICRO.': 1e-3}.get(m.group(1), 1.0)
    return 1.0


def read(path):
    s = read_mm(path)
    f = file_unit_mm(path)
    if f != 1.0:
        t = gp_Trsf()
        t.SetScale(gp_Pnt(0, 0, 0), 1.0 / f)
        s = BRepBuilderAPI_Transform(s, t, True).Shape()
    return s


def read_mm(path):
    r = STEPControl_Reader()
    st = r.ReadFile(path)
    if st != IFSelect_RetDone:
        raise RuntimeError('ReadFile status %s' % st)
    r.TransferRoots()
    return r.OneShape()


def largest_solid(s):
    sol = items(s, TopAbs_SOLID)
    if not sol:
        raise RuntimeError('no solid in file')
    return max(sol, key=lambda x: abs(volume(x)))


def build(spec):
    parts = spec.split('|')
    kind, arg = parts[0].split('=', 1)
    if kind == 'step':
        s = largest_solid(read(arg))
    else:
        v = [float(x) for x in arg.split(',')]
        if kind == 'box':
            s = BRepPrimAPI_MakeBox(gp_Pnt(-v[0] / 2, -v[1] / 2, -v[2] / 2), v[0], v[1], v[2]).Shape()
        elif kind == 'cyl':
            s = BRepPrimAPI_MakeCylinder(v[0], v[1]).Shape()
        elif kind == 'cone':
            s = BRepPrimAPI_MakeCone(v[0], 0.0, v[1]).Shape()
        elif kind == 'sph':
            s = BRepPrimAPI_MakeSphere(v[0]).Shape()
        else:
            raise RuntimeError('unknown spec ' + kind)
    for p in parts[1:]:
        v = [float(x) for x in p[2:].split(',')]
        t = gp_Trsf()
        if p[0] == 't':
            t.SetTranslation(gp_Vec(v[0], v[1], v[2]))
        else:
            t.SetRotation(gp_Ax1(gp_Pnt(v[4], v[5], v[6]), gp_Dir(v[0], v[1], v[2])), math.radians(v[3]))
        s = BRepBuilderAPI_Transform(s, t, True).Shape()
    return s


def kinds(s):
    n = [0] * 6
    for f in items(s, TopAbs_FACE):
        t = BRepAdaptor_Surface(TopoDS.Face(f)).GetType()
        k = {GeomAbs_Plane: 0, GeomAbs_Sphere: 1, GeomAbs_Cylinder: 2, GeomAbs_Cone: 3, GeomAbs_Torus: 4}.get(t, 5)
        n[k] += 1
    return ','.join(map(str, n))


def dump(s):
    BRepMesh_IncrementalMesh(s, 0.002 * diag(s), False, 0.2)
    pos, idx, edges, verts = [], [], [], []
    base = 0
    for f in items(s, TopAbs_FACE):
        face = TopoDS.Face(f)
        loc = TopLoc_Location()
        t = BRep_Tool.Triangulation_s(face, loc)
        if t is None:
            continue
        tr = loc.Transformation()
        for i in range(1, t.NbNodes() + 1):
            p = t.Node(i).Transformed(tr)
            pos += [p.X(), p.Y(), p.Z()]
        rev = face.Orientation() == TopAbs_REVERSED
        for i in range(1, t.NbTriangles() + 1):
            a, b, c = t.Triangle(i).Get()
            if rev:
                b, c = c, b
            idx += [base + a - 1, base + b - 1, base + c - 1]
        base += t.NbNodes()
    m = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(s, TopAbs_EDGE, m)
    for i in range(1, m.Extent() + 1):
        e = TopoDS.Edge(m.FindKey(i))
        if BRep_Tool.Degenerated_s(e):
            continue
        c = BRepAdaptor_Curve(e)
        a, b = c.FirstParameter(), c.LastParameter()
        line = []
        for k in range(49):
            p = c.Value(a + (b - a) * k / 48.0)
            line += [p.X(), p.Y(), p.Z()]
        edges.append(line)
    vm = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(s, TopAbs_VERTEX, vm)
    for i in range(1, vm.Extent() + 1):
        p = BRep_Tool.Pnt_s(TopoDS.Vertex(vm.FindKey(i)))
        verts += [p.X(), p.Y(), p.Z()]
    r = lambda v: [round(x, 6) for x in v]
    return {'pos': r(pos), 'idx': idx, 'edges': [r(e) for e in edges], 'verts': r(verts),
            'counts': [count(s, TopAbs_FACE), count(s, TopAbs_EDGE), count(s, TopAbs_VERTEX)]}


def diag(s):
    b = Bnd_Box()
    BRepBndLib.Add_s(s, b)
    if b.IsVoid():
        return 1.0
    p0, p1 = b.CornerMin(), b.CornerMax()
    x0, y0, z0, x1, y1, z1 = p0.X(), p0.Y(), p0.Z(), p1.X(), p1.Y(), p1.Z()
    return math.dist((x0, y0, z0), (x1, y1, z1))


def main():
    mode = sys.argv[1]
    if mode == 'load':
        path = sys.argv[2]
        t0 = time.perf_counter()
        try:
            s = read(path)
        except Exception as e:
            print('LOAD', path, 'FAIL read_s', time.perf_counter() - t0, 'solids 0 shells 0', e)
            return
        sec = time.perf_counter() - t0
        sol = items(s, TopAbs_SOLID)
        print('LOAD', path, 'ok read_s %.6g' % sec, 'solids', len(sol), 'shells', count(s, TopAbs_SHELL), flush=True)
        for i, x in enumerate(sol):
            t1 = time.perf_counter()
            v = volume(x)
            print('SOLID', path, i, count(x, TopAbs_FACE), count(x, TopAbs_EDGE), count(x, TopAbs_VERTEX),
                  int(BRepCheck_Analyzer(x).IsValid()), 'kinds=' + kinds(x), '%.6g' % (time.perf_counter() - t1), '%.12g' % v, flush=True)
        return
    if mode == 'chain':
        body = build(sys.argv[2])
        q = [float(x) for x in sys.argv[3].split(',')]
        t = gp_Trsf()
        t.SetRotation(gp_Ax1(gp_Pnt(q[4], q[5], q[6]), gp_Dir(q[0], q[1], q[2])), math.radians(q[3]))
        for it in range(1, int(sys.argv[4]) + 1):
            other = BRepBuilderAPI_Transform(body, t, True).Shape()
            t0 = time.perf_counter()
            algo = BRepAlgoAPI_Common(body, other)
            r = algo.Shape()
            sec = time.perf_counter() - t0
            if not algo.IsDone():
                print('CHAIN', it, 'FAIL %.6g' % sec, '0 0 0 0 0 - - NotDone', flush=True)
                return
            body = r
            print('CHAIN', it, 'ok %.6g' % sec, count(r, TopAbs_FACE), count(r, TopAbs_EDGE), count(r, TopAbs_VERTEX),
                  int(BRepCheck_Analyzer(r).IsValid()), len(items(r, TopAbs_SOLID)), '0', '%.12g' % volume(r), flush=True)
            if count(r, TopAbs_FACE) == 0:
                return
        return
    if mode == 'bool':
        try:
            a, b = build(sys.argv[2]), build(sys.argv[3])
        except Exception as e:
            for op in ['intersection', 'union', 'a-b', 'b-a', 'xor']:
                print('BOOL', op, 'LOADFAIL 0 0 0 0 0 0 - -', e, flush=True)
            return
        prefix = sys.argv[4] if len(sys.argv) > 4 else None
        dumps = [dump(a), dump(b)] if prefix else None
        for op in ['intersection', 'union', 'a-b', 'b-a', 'xor']:
            t0 = time.perf_counter()
            try:
                if op == 'intersection':
                    algo = BRepAlgoAPI_Common(a, b)
                elif op == 'union':
                    algo = BRepAlgoAPI_Fuse(a, b)
                elif op == 'a-b':
                    algo = BRepAlgoAPI_Cut(a, b)
                elif op == 'b-a':
                    algo = BRepAlgoAPI_Cut(b, a)
                else:
                    c1, c2 = BRepAlgoAPI_Cut(a, b), BRepAlgoAPI_Cut(b, a)
                    algo = BRepAlgoAPI_Fuse(c1.Shape(), c2.Shape())
                r = algo.Shape()
                sec = time.perf_counter() - t0
                err = not algo.IsDone()
                warn = False
            except Exception as e:
                print('BOOL', op, 'FAIL %.6g' % (time.perf_counter() - t0), '0 0 0 0 0 - -', str(e)[:200], flush=True)
                if dumps is not None:
                    dumps.append({'pos': [], 'idx': [], 'edges': [], 'verts': [], 'counts': [0, 0, 0]})
                continue
            if err:
                print('BOOL', op, 'FAIL %.6g' % sec, '0 0 0 0 0 - - NotDone', flush=True)
                if dumps is not None:
                    dumps.append({'pos': [], 'idx': [], 'edges': [], 'verts': [], 'counts': [0, 0, 0]})
                continue
            valid = int(BRepCheck_Analyzer(r).IsValid())
            t1 = time.perf_counter()
            v = volume(r) if count(r, TopAbs_FACE) else 0.0
            print('BOOL', op, 'ok %.6g' % sec, count(r, TopAbs_FACE), count(r, TopAbs_EDGE), count(r, TopAbs_VERTEX), valid,
                  len(items(r, TopAbs_SOLID)), '%.6g' % (time.perf_counter() - t1), '%.12g' % v, 'warn' if warn else '', flush=True)
            if dumps is not None:
                dumps.append(dump(r))
        if prefix:
            json.dump(dumps, open(prefix, 'w'))


if __name__ == '__main__':
    main()
