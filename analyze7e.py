import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]

def get_pts(pl):
    c = pl._coords
    pts = [(c[i], c[i+1], c[i+2]) for i in range(0, len(c), 3)]
    return pts  # raw, including closing point

def seg_lengths(pts):
    return [round(math.dist(pts[i], pts[(i+1) % len(pts)]), 2) for i in range(len(pts)-1)]

def z_range(pts):
    zs = [p[2] for p in pts]
    return min(zs), max(zs)

bad = [0, 1, 2, 34, 36, 43, 54, 81]
good = [10, 20, 30, 40, 60, 70]

print("=== BAD bot polylines ===")
for idx in bad:
    pts = get_pts(bots[idx])
    zmin, zmax = z_range(pts)
    n_raw = len(pts)
    closed = math.dist(pts[0], pts[-1]) < 1e-6
    segs = seg_lengths(pts)
    print(f"bot[{idx:2d}]: n={n_raw} closed={closed} z=[{zmin:.1f},{zmax:.1f}] segs={segs}")
    print(f"  coords: {[tuple(round(x,1) for x in p) for p in pts]}")

print("\n=== GOOD bot polylines ===")
for idx in good:
    pts = get_pts(bots[idx])
    zmin, zmax = z_range(pts)
    n_raw = len(pts)
    closed = math.dist(pts[0], pts[-1]) < 1e-6
    segs = seg_lengths(pts)
    print(f"bot[{idx:2d}]: n={n_raw} closed={closed} z=[{zmin:.1f},{zmax:.1f}] segs={segs}")
    print(f"  coords: {[tuple(round(x,1) for x in p) for p in pts]}")
