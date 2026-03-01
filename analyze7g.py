import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]

def get_pts(pl):
    c = pl._coords
    pts = [(c[i], c[i+1], c[i+2]) for i in range(0, len(c), 3)]
    if len(pts) >= 2 and math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts

def seg_lengths(pts):
    n = len(pts)
    return [round(math.dist(pts[i], pts[(i+1)%n]), 3) for i in range(n)]

def min_seg(pts):
    return min(math.dist(pts[i], pts[(i+1)%len(pts)]) for i in range(len(pts)))

def is_coplanar(pts, tol=1e-3):
    if len(pts) < 4:
        return True
    # Fit plane through first 3, check remaining
    a, b, c = pts[0], pts[1], pts[2]
    ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
    ac = (c[0]-a[0], c[1]-a[1], c[2]-a[2])
    nx = ab[1]*ac[2]-ab[2]*ac[1]; ny = ab[2]*ac[0]-ab[0]*ac[2]; nz = ab[0]*ac[1]-ab[1]*ac[0]
    nl = math.sqrt(nx*nx+ny*ny+nz*nz)
    if nl < 1e-12: return True
    nx/=nl; ny/=nl; nz/=nl
    for p in pts[3:]:
        d = abs((p[0]-a[0])*nx + (p[1]-a[1])*ny + (p[2]-a[2])*nz)
        if d > tol:
            return False
    return True

print("=== TOP polylines at bad indices (0,1,2,34,36,43,54,81) ===")
for idx in [0,1,2,34,36,43,54,81]:
    if idx >= len(tops): print(f"top[{idx}]: OUT OF RANGE"); continue
    pts = get_pts(tops[idx])
    segs = seg_lengths(pts)
    minseg = min_seg(pts)
    coplanar = is_coplanar(pts)
    print(f"top[{idx:2d}]: n={len(pts)} min_seg={minseg:.3f} coplanar={coplanar}")
    print(f"  segs={segs}")

print("\n=== TOP polylines at good indices ===")
for idx in [10,20,30,40,60,70]:
    pts = get_pts(tops[idx])
    segs = seg_lengths(pts)
    minseg = min_seg(pts)
    coplanar = is_coplanar(pts)
    print(f"top[{idx:2d}]: n={len(pts)} min_seg={minseg:.3f} coplanar={coplanar}")
    print(f"  segs={segs}")

# Also check: which top polylines are non-planar with large deviation?
print("\n=== All top polylines: planarity deviation ===")
def max_plane_dev(pts):
    if len(pts) < 4: return 0.0
    a,b,c = pts[0],pts[1],pts[2]
    ab=(b[0]-a[0],b[1]-a[1],b[2]-a[2]); ac=(c[0]-a[0],c[1]-a[1],c[2]-a[2])
    nx=ab[1]*ac[2]-ab[2]*ac[1]; ny=ab[2]*ac[0]-ab[0]*ac[2]; nz=ab[0]*ac[1]-ab[1]*ac[0]
    nl=math.sqrt(nx*nx+ny*ny+nz*nz)
    if nl<1e-12: return 0.0
    nx/=nl; ny/=nl; nz/=nl
    return max(abs((p[0]-a[0])*nx+(p[1]-a[1])*ny+(p[2]-a[2])*nz) for p in pts[3:])

devs = [(i, max_plane_dev(get_pts(tops[i])), len(get_pts(tops[i]))) for i in range(len(tops))]
# Sort by deviation descending
devs.sort(key=lambda x: -x[1])
print("Top 15 most non-planar top polylines:")
for idx, dev, n in devs[:15]:
    marker = " <-- BAD" if idx in [0,1,2,34,36,43,54,81] else ""
    print(f"  top[{idx:2d}]: n={n} max_plane_dev={dev:.2f}{marker}")
