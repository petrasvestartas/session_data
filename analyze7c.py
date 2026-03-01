import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7.pb'
obj = Objects.pb_load(fname)
tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]

def centroid(pl):
    c = pl._coords
    pts = [(c[i], c[i+1], c[i+2]) for i in range(0, len(c), 3)]
    n = len(pts)
    return (sum(p[0] for p in pts)/n, sum(p[1] for p in pts)/n, sum(p[2] for p in pts)/n)

top_cents = [centroid(t) for t in tops]
bot_cents = [centroid(b) for b in bots]

# Simulate greedy 1-to-1 matching (same order as C++: top face keys ascending = polyline order)
bot_used = [False] * len(bots)
matching = []  # (top_idx, bot_idx, dist)
for ti, tc in enumerate(top_cents):
    best_d = 1e300
    best_bi = 0
    for bi, bc in enumerate(bot_cents):
        if bot_used[bi]: continue
        d = math.dist(tc, bc)
        if d < best_d:
            best_d = d
            best_bi = bi
    bot_used[best_bi] = True
    matching.append((ti, best_bi, best_d))

bad = {0,1,2,34,36,43,54,81}
print("Panel | top_idx | bot_idx | dist   | top_idx==bot_idx?")
for panel_i, (ti, bi, d) in enumerate(matching):
    if panel_i in bad or (ti != bi):
        tag = "BAD " if panel_i in bad else "    "
        match = "YES" if ti == bi else f"NO (bot={bi})"
        print(f"{tag} panel {panel_i:3d}: top {ti:3d} -> bot {bi:3d}  dist={d:.1f}  {match}")

# Also check: for bad panels, what is the distance vs what the "correct" (same index) bot would be
print("\n--- Distance comparison for bad panels ---")
for panel_i, (ti, bi, d) in enumerate(matching):
    if panel_i in bad:
        correct_d = math.dist(top_cents[ti], bot_cents[ti]) if ti < len(bots) else float('nan')
        print(f"panel {panel_i}: matched bot {bi} (d={d:.1f}), correct bot {ti} would be d={correct_d:.1f}")
