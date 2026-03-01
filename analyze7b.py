import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]

APPROXIMATION = 0.001
ZERO_TOLERANCE = 1e-10

def merge_collinear(pts):
    zt2 = ZERO_TOLERANCE * ZERO_TOLERANCE
    tol = APPROXIMATION
    changed = True
    while changed:
        changed = False
        m = len(pts)
        if m < 3:
            break
        np2 = []
        for i in range(m):
            p = pts[(i-1) % m]
            cur = pts[i]
            nx = pts[(i+1) % m]
            ax, ay, az = cur[0]-p[0], cur[1]-p[1], cur[2]-p[2]
            bx, by, bz = nx[0]-cur[0], nx[1]-cur[1], nx[2]-cur[2]
            cx = ay*bz - az*by
            cy = az*bx - ax*bz
            cz = ax*by - ay*bx
            a2 = ax*ax + ay*ay + az*az
            b2 = bx*bx + by*by + bz*bz
            if a2 < zt2 or b2 < zt2 or cx*cx+cy*cy+cz*cz < tol*tol*a2*b2:
                changed = True
            else:
                np2.append(cur)
        pts = np2
    return pts

def get_pts(pl):
    c = pl._coords
    pts = [(c[i], c[i+1], c[i+2]) for i in range(0, len(c), 3)]
    # remove duplicate last point (closed polyline)
    if len(pts) >= 2 and math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts

# Simulate the build_panel merge step for bad and good indices
print("idx | top_raw -> merged | bot_raw -> merged")
for idx in [0, 1, 2, 34, 36, 43, 54, 81, 10, 20, 30, 40, 50, 60, 70]:
    if idx >= len(tops): continue
    tp = get_pts(tops[idx])
    bp = get_pts(bots[idx])
    tm = merge_collinear(list(tp))
    bm = merge_collinear(list(bp))
    bad = "BAD " if idx in [0,1,2,34,36,43,54,81] else "GOOD"
    print(f"{bad} idx {idx:2d}: top {len(tp)}->{len(tm)}  bot {len(bp)}->{len(bm)}")
