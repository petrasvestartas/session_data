import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]

APPROXIMATION = 1e-3
ZERO_TOLERANCE = 1e-12

def get_pts(pl):
    c = pl._coords
    pts = [(c[i], c[i+1], c[i+2]) for i in range(0, len(c), 3)]
    if len(pts) >= 2 and math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts

def merge_collinear(pts):
    zt2 = ZERO_TOLERANCE * ZERO_TOLERANCE
    tol = APPROXIMATION
    changed = True
    while changed:
        changed = False
        m = len(pts)
        if m < 3: break
        np2 = []
        for i in range(m):
            p = pts[(i-1) % m]; cur = pts[i]; nx = pts[(i+1) % m]
            ax, ay, az = cur[0]-p[0], cur[1]-p[1], cur[2]-p[2]
            bx, by, bz = nx[0]-cur[0], nx[1]-cur[1], nx[2]-cur[2]
            cx = ay*bz - az*by; cy = az*bx - ax*bz; cz = ax*by - ay*bx
            a2 = ax*ax + ay*ay + az*az; b2 = bx*bx + by*by + bz*bz
            if a2 < zt2 or b2 < zt2 or cx*cx+cy*cy+cz*cz < tol*tol*a2*b2:
                changed = True
            else:
                np2.append(cur)
        pts = np2
    return pts

def newell_normal(pts):
    nx=ny=nz=0.0
    n=len(pts)
    for i in range(n):
        a=pts[i]; b=pts[(i+1)%n]
        nx += (a[1]-b[1])*(a[2]+b[2])
        ny += (a[2]-b[2])*(a[0]+b[0])
        nz += (a[0]-b[0])*(a[1]+b[1])
    return (nx,ny,nz)

def simulate_panel(idx, label):
    tp = merge_collinear(get_pts(tops[idx]))
    bp = merge_collinear(get_pts(bots[idx]))
    n = len(tp); m = len(bp)

    tcx = sum(p[0] for p in tp)/n; tcy = sum(p[1] for p in tp)/n; tcz = sum(p[2] for p in tp)/n
    bcx = sum(p[0] for p in bp)/m; bcy = sum(p[1] for p in bp)/m; bcz = sum(p[2] for p in bp)/m
    ax=tcx-bcx; ay=tcy-bcy; az=tcz-bcz
    alen = math.sqrt(ax*ax+ay*ay+az*az)
    if alen > 1e-12: ax/=alen; ay/=alen; az/=alen

    tnx,tny,tnz = newell_normal(tp)
    tdot = tnx*ax+tny*ay+tnz*az
    if tdot < 0: tp = list(reversed(tp))

    bnx,bny,bnz = newell_normal(bp)
    bdot = bnx*ax+bny*ay+bnz*az
    if bdot < 0: bp = list(reversed(bp))

    # Compute midpoints
    top_mids = [((tp[i][0]+tp[(i+1)%n][0])*0.5, (tp[i][1]+tp[(i+1)%n][1])*0.5, (tp[i][2]+tp[(i+1)%n][2])*0.5) for i in range(n)]
    bot_mids = [((bp[j][0]+bp[(j+1)%m][0])*0.5, (bp[j][1]+bp[(j+1)%m][1])*0.5, (bp[j][2]+bp[(j+1)%m][2])*0.5) for j in range(m)]

    # bot_to_top matching
    bot_to_top = [min(range(n), key=lambda i: math.dist(bot_mids[j], top_mids[i])) for j in range(m)]
    bot_dist   = [math.dist(bot_mids[j], top_mids[bot_to_top[j]]) for j in range(m)]
    top_to_bot = [min(range(m), key=lambda j: math.dist(top_mids[i], bot_mids[j])) for i in range(n)]

    avg = sum(bot_dist) / m
    threshold = avg * 2.0

    top_used = [False]*n
    quads = 0; tris_bot = 0; tris_top = 0
    for j in range(m):
        ti = bot_to_top[j]
        if bot_dist[j] <= threshold and top_to_bot[ti] == j:
            quads += 1
            top_used[ti] = True
        else:
            tris_bot += 1
    for i in range(n):
        if not top_used[i]:
            tris_top += 1

    total_wall = quads + tris_bot + tris_top
    print(f"{label} idx {idx}: n={n} m={m}  axis=({ax:.3f},{ay:.3f},{az:.3f})  tdot={tdot:.1f}  bdot={bdot:.1f}")
    print(f"  bot_dist min={min(bot_dist):.1f} max={max(bot_dist):.1f} avg={avg:.1f} threshold={threshold:.1f}")
    print(f"  quads={quads} tris_bot={tris_bot} tris_top={tris_top} total_wall={total_wall}")
    print(f"  bot_to_top={bot_to_top}")
    print(f"  top_to_bot={top_to_bot}")
    print()

for idx in [0, 1, 2, 34, 36, 43, 54, 81]:
    simulate_panel(idx, "BAD ")
for idx in [10, 20, 60, 70]:
    simulate_panel(idx, "GOOD")
