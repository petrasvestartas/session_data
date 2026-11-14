# Boolean cases of the STEP bench, one tab-separated line each: id, specA, specB, group, part.
#   gen_cases.py <bench_root> <occt_load.txt> > cases.tsv
# Placement from the OCCT bounding box of the largest solid in file units (the same numbers both kernels see).
import sys, os, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
import importlib.util
spec = importlib.util.spec_from_file_location('ob', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'occt_step_bench.py'))
ob = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ob)

root, occt_load = sys.argv[1], sys.argv[2]
solids = {}
for line in open(occt_load):
    w = line.split()
    if w and w[0] == 'LOAD':
        solids[w[1]] = int(w[6]) if w[2] == 'ok' else 0


def fmt(v):
    return ','.join('%.9g' % x for x in v)


def bbox(path):
    s = ob.largest_solid(ob.read(path))
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s, b, False, False)
    p0, p1 = b.CornerMin(), b.CornerMax()
    return [p0.X(), p0.Y(), p0.Z()], [p1.X(), p1.Y(), p1.Z()]


out = []
for path in sorted(solids):
    if solids[path] < 1:
        continue
    rel = os.path.relpath(path, root)
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', rel.replace('/', '__')).rsplit('.', 1)[0]
    lo, hi = bbox(path)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    d = [hi[i] - lo[i] for i in range(3)]
    A = 'step=' + path
    # rotated copies of the part about axes through its box centre (occt-booltest style)
    out.append((name + '#rot30x', A, A + '|r=1,0,0,30,' + fmt(c), 'rot', rel))
    out.append((name + '#rot5z', A, A + '|r=0,0,1,5,' + fmt(c), 'rot', rel))
    # a slab across the longest box direction through the centre (cuts every part that spans that direction), turned off the part's planes
    kl = max(range(3), key=lambda i: d[i])
    bs = [0.3 * d[i] if i == kl else 1.2 * d[i] for i in range(3)]
    bc = [c[i] + (0.05 * d[i] if i == kl else 0.0) for i in range(3)]
    out.append((name + '#box', A, 'box=' + fmt(bs) + '|r=1,2,3,10,0,0,0|t=' + fmt(bc), 'cutter', rel))
    # a cylinder along the shortest box direction through the centre (through holes and bosses of plates)
    k = min(range(3), key=lambda i: d[i])
    others = [d[i] for i in range(3) if i != k]
    r = 0.12 * min(others)
    h = 1.6 * d[k] + 2 * r
    turn = {0: '|r=0,1,0,90,0,0,0', 1: '|r=1,0,0,-90,0,0,0', 2: ''}[k]
    out.append((name + '#cyl', A, 'cyl=%.9g,%.9g|t=0,0,%.9g' % (r, h, -h / 2) + turn + '|t=' + fmt(c), 'cutter', rel))
    # a sphere on a box corner region
    sr = 0.3 * min(d)
    sc = [c[i] - 0.3 * d[i] for i in range(3)]
    out.append((name + '#sph', A, 'sph=%.9g|t=' % sr + fmt(sc), 'cutter', rel))
for row in out:
    print('\t'.join(row))
