import xml.etree.ElementTree as ET, os, math
COORDS_FILE = "WoodF2F_top_to_top_pairs.pb_coords.txt"
WOOD_XML    = "ref_top_to_top_pairs.xml"
TOL         = 0.5
our = {}
if not os.path.exists(COORDS_FILE): print(f"ERROR: {COORDS_FILE} not found"); exit(1)
with open(COORDS_FILE) as f:
    ei = -1
    for line in f:
        line = line.strip()
        if line.startswith("element "): ei = int(line.split()[1]); our[ei] = []
        elif line.startswith("poly ") and ei >= 0:
            after = line.split(":",1)[1].strip()
            if not after: our[ei].append([]); continue
            nums = list(map(float, after.split()))
            our[ei].append([(nums[i],nums[i+1],nums[i+2]) for i in range(0,len(nums)-2,3)])
if not os.path.exists(WOOD_XML): print(f"ERROR: {WOOD_XML} not found"); exit(1)
tree = ET.parse(WOOD_XML); root = tree.getroot()
wood_ref = {}
for gi, g in enumerate(root.findall("polyline_group")):
    pts_list = []
    for p in g.findall("polyline"):
        pts_list.append([(float(pt.find("x").text),float(pt.find("y").text),float(pt.find("z").text)) for pt in p.findall("point")])
    wood_ref[gi] = pts_list
print(f"Our: {len(our)}  Wood: {len(wood_ref)}")
ok = fail = 0
for ei in sorted(our.keys()):
    ours = our[ei]; ref = wood_ref.get(ei, [])
    if len(ours) != len(ref): print(f"el {ei:2d}: POLY MISMATCH ours={len(ours)} wood={len(ref)}"); fail += 1; continue
    el_ok = True
    for pi,(op,rp) in enumerate(zip(ours,ref)):
        if len(op) != len(rp): print(f"el {ei:2d} p{pi}: PT MISMATCH ours={len(op)} wood={len(rp)}"); el_ok=False; fail+=1; continue
        if not op: continue
        d = max(math.sqrt((ox-rx)**2+(oy-ry)**2+(oz-rz)**2) for (ox,oy,oz),(rx,ry,rz) in zip(op,rp))
        if d > TOL: print(f"el {ei:2d} p{pi}: dev={d:.3f}mm pts={len(op)}"); el_ok=False; fail+=1
    if el_ok: ok+=1
print(f"\n{ok}/{len(our)} pass (tol={TOL}mm), {fail} fail")
