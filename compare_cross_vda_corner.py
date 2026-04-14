"""
Compare main_5 cross_vda_corner output against wood's reference.
Usage: cd session_data && python compare_cross_vda_corner.py
Wood reference: ref_cross_vda_corner.xml
Our output:     WoodF2F_cross_vda_corner.pb_coords.txt
"""
import xml.etree.ElementTree as ET
import os, math

COORDS_FILE = "WoodF2F_cross_vda_corner.pb_coords.txt"
WOOD_XML    = "ref_cross_vda_corner.xml"
TOL         = 0.5  # mm

our = {}
if not os.path.exists(COORDS_FILE):
    print(f"ERROR: {COORDS_FILE} not found — build+run main_5 first")
    exit(1)

with open(COORDS_FILE) as f:
    ei = -1
    for line in f:
        line = line.strip()
        if line.startswith("element "):
            ei = int(line.split()[1])
            our[ei] = []
        elif line.startswith("poly ") and ei >= 0:
            after_colon = line.split(":", 1)[1].strip()
            if not after_colon:
                our[ei].append([])
                continue
            nums = list(map(float, after_colon.split()))
            pts = [(nums[i], nums[i+1], nums[i+2]) for i in range(0, len(nums)-2, 3)]
            our[ei].append(pts)

if not os.path.exists(WOOD_XML):
    print(f"ERROR: {WOOD_XML} not found")
    exit(1)

tree = ET.parse(WOOD_XML)
root = tree.getroot()
groups = root.findall("polyline_group")
wood_ref = {}
for gi, g in enumerate(groups):
    polys = g.findall("polyline")
    pts_list = []
    for p in polys:
        pts = [(float(pt.find("x").text),
                float(pt.find("y").text),
                float(pt.find("z").text))
               for pt in p.findall("point")]
        pts_list.append(pts)
    wood_ref[gi] = pts_list

print(f"Our elements:  {len(our)}")
print(f"Wood elements: {len(wood_ref)}")
if len(our) != len(wood_ref):
    print("ELEMENT COUNT MISMATCH")

ok = 0
fail = 0
for ei in sorted(our.keys()):
    ours = our[ei]
    ref  = wood_ref.get(ei, [])
    if len(ours) != len(ref):
        print(f"el {ei:2d}: POLY COUNT MISMATCH  ours={len(ours)}  wood={len(ref)}")
        fail += 1
        continue
    el_ok = True
    for pi, (op, rp) in enumerate(zip(ours, ref)):
        if len(op) != len(rp):
            print(f"el {ei:2d} poly {pi}: PT COUNT MISMATCH  ours={len(op)}  wood={len(rp)}")
            el_ok = False
            fail += 1
            continue
        if not op:
            continue
        max_dev = max(math.sqrt((ox-rx)**2+(oy-ry)**2+(oz-rz)**2)
                      for (ox,oy,oz),(rx,ry,rz) in zip(op, rp))
        if max_dev > TOL:
            print(f"el {ei:2d} poly {pi}: max_dev={max_dev:.3f}mm  pts={len(op)}")
            el_ok = False
            fail += 1
    if el_ok:
        ok += 1

print(f"\n{ok}/{len(our)} elements pass (tol={TOL}mm), {fail} failures")
