import re
import math

PATH = r"C:\brg\code_rust\session\session_data\WoodF2F_annen_corner_custom.pb_coords.txt"

def parse(path):
    elems = {}
    cur = None
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            m_e = re.match(r"element (\d+)", line)
            if m_e:
                cur = int(m_e.group(1))
                elems[cur] = []
                continue
            m_p = re.match(r"\s+poly \d+:\s*(.*)$", line)
            if m_p:
                nums = [float(x) for x in m_p.group(1).split()]
                pts = [(nums[i], nums[i+1], nums[i+2]) for i in range(0, len(nums), 3)]
                elems[cur].append(pts)
    return elems

def centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts)/n, sum(p[1] for p in pts)/n, sum(p[2] for p in pts)/n)

def cov3(pts, c):
    sxx=sxy=sxz=syy=syz=szz=0.0
    for p in pts:
        dx,dy,dz = p[0]-c[0], p[1]-c[1], p[2]-c[2]
        sxx+=dx*dx; sxy+=dx*dy; sxz+=dx*dz
        syy+=dy*dy; syz+=dy*dz; szz+=dz*dz
    return [[sxx,sxy,sxz],[sxy,syy,syz],[sxz,syz,szz]]

def smallest_eigvec(M):
    # 3x3 symmetric; power iteration on (tr*I - M) to find smallest eigvec
    tr = M[0][0] + M[1][1] + M[2][2]
    A = [[tr-M[i][j] if i==j else -M[i][j] for j in range(3)] for i in range(3)]
    v = [1.0, 0.3, 0.7]
    for _ in range(200):
        nv = [A[i][0]*v[0]+A[i][1]*v[1]+A[i][2]*v[2] for i in range(3)]
        n = math.sqrt(sum(x*x for x in nv))
        if n < 1e-30: break
        v = [x/n for x in nv]
    return tuple(v)

def fit_plane(pts):
    c = centroid(pts)
    M = cov3(pts, c)
    n = smallest_eigvec(M)
    nn = math.sqrt(sum(x*x for x in n))
    n = (n[0]/nn, n[1]/nn, n[2]/nn)
    return c, n

def signed_dist(p, c, n):
    return (p[0]-c[0])*n[0] + (p[1]-c[1])*n[1] + (p[2]-c[2])*n[2]

elems = parse(PATH)

def strip_closing(pts):
    if len(pts) > 1 and max(abs(pts[0][i]-pts[-1][i]) for i in range(3)) < 1e-9:
        return pts[:-1]
    return pts

print(f"{'='*70}\nCoplanarity test for WoodF2F_annen_corner_custom.pb\n{'='*70}")

for ei, polys in elems.items():
    n_p = len(polys)
    if n_p < 4:
        print(f"\nelement {ei}: {n_p} polylines — no holes, skipping")
        continue
    # Layout: [hole0_top, hole0_bot, ..., outer_top, outer_bot]
    outer_top = strip_closing(polys[-2])
    outer_bot = strip_closing(polys[-1])
    hole_tops = [strip_closing(polys[i]) for i in range(0, n_p-2, 2)]
    hole_bots = [strip_closing(polys[i+1]) for i in range(0, n_p-2, 2)]

    print(f"\nelement {ei}: outer={len(outer_top)}pts, holes={len(hole_tops)}")

    # --- Fit plane from OUTER TOP only (what Mesh::loft does) ---
    c_t, n_t = fit_plane(outer_top)
    # Flatness of outer_top itself
    outer_dev = max(abs(signed_dist(p, c_t, n_t)) for p in outer_top)
    print(f"  outer_top plane normal=({n_t[0]:+.4f},{n_t[1]:+.4f},{n_t[2]:+.4f})  "
          f"outer self-flatness max |d|={outer_dev:.3e}")

    # Distance of every hole vertex to the outer's plane
    max_top = 0.0
    for hi, h in enumerate(hole_tops):
        hd = max(abs(signed_dist(p, c_t, n_t)) for p in h)
        max_top = max(max_top, hd)
        print(f"  hole{hi}_top to outer-top plane:  max |d| = {hd:.3e}")

    # --- Do the same for BOT side ---
    c_b, n_b = fit_plane(outer_bot)
    outer_bot_dev = max(abs(signed_dist(p, c_b, n_b)) for p in outer_bot)
    print(f"  outer_bot plane normal=({n_b[0]:+.4f},{n_b[1]:+.4f},{n_b[2]:+.4f})  "
          f"outer_bot self-flatness max |d|={outer_bot_dev:.3e}")
    max_bot = 0.0
    for hi, h in enumerate(hole_bots):
        hd = max(abs(signed_dist(p, c_b, n_b)) for p in h)
        max_bot = max(max_bot, hd)
        print(f"  hole{hi}_bot to outer-bot plane:  max |d| = {hd:.3e}")

    # --- Endpoint closure: did get_open_points actually strip? ---
    # Mesh::loft uses 1e-12 tolerance. Let's measure actual closure gap.
    for i, p in enumerate(polys):
        gap = max(abs(p[0][j]-p[-1][j]) for j in range(3))
        if gap > 1e-12 and gap < 1e-6:
            print(f"  !! poly {i} closure gap = {gap:.3e} — above 1e-12, below 1e-6 (DANGEROUS)")
        elif gap < 1e-12:
            pass  # stripped fine
        else:
            pass  # open polyline

    print(f"  >> max hole deviation: top={max_top:.3e}, bot={max_bot:.3e}")
