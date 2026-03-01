import sys
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects
import math

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]

bad_indices = [54, 43, 0, 1, 2, 34, 36, 81]
good_indices = [10, 20, 30, 40, 50, 60, 70]

def analyze(pl):
    coords = pl._coords
    pts = [(coords[i], coords[i+1], coords[i+2]) for i in range(0, len(coords), 3)]
    n = len(pts)
    # Check if closed (first == last)
    closed = math.dist(pts[0], pts[-1]) < 1e-6 if n > 1 else False
    # Compute bounding box size
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    bbox = (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
    # Compute perimeter
    perim = sum(math.dist(pts[i], pts[(i+1)%n]) for i in range(n))
    # Check collinearity: cross product of consecutive edges
    max_cross = 0
    for i in range(n):
        a = pts[i]; b = pts[(i+1)%n]; c = pts[(i+2)%n]
        ab = (b[0]-a[0], b[1]-a[1], b[2]-a[2])
        bc = (c[0]-b[0], c[1]-b[1], c[2]-b[2])
        cross = (ab[1]*bc[2]-ab[2]*bc[1], ab[2]*bc[0]-ab[0]*bc[2], ab[0]*bc[1]-ab[1]*bc[0])
        cross_mag = math.sqrt(cross[0]**2+cross[1]**2+cross[2]**2)
        max_cross = max(max_cross, cross_mag)
    return {'n': n, 'closed': closed, 'bbox': bbox, 'perim': round(perim,3), 'max_cross': round(max_cross,6)}

print("=== BAD indices ===")
for idx in bad_indices:
    if idx < len(tops):
        t = analyze(tops[idx])
        b = analyze(bots[idx])
        print(f"idx {idx}: top={t}  bot={b}")

print("\n=== GOOD indices ===")
for idx in good_indices:
    if idx < len(tops):
        t = analyze(tops[idx])
        b = analyze(bots[idx])
        print(f"idx {idx}: top={t}  bot={b}")
