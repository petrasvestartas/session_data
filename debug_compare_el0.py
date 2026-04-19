"""Debug comparison for element 0, printing individual point deviations."""
import xml.etree.ElementTree as ET
import math

COORDS_FILE = "WoodF2F_vidy_one_axis_two_layers.pb_coords.txt"
WOOD_XML    = "C:/brg/code_cpp/wood/cmake/src/wood/dataset/out.xml"

our = {}
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

tree = ET.parse(WOOD_XML)
root = tree.getroot()
groups = root.findall("polyline_group")
wood_ref = {}
for gi, g in enumerate(groups):
    polys = g.findall("polyline")
    pts_list = []
    for p in polys:
        pts = [(float(pt.find("x").text), float(pt.find("y").text), float(pt.find("z").text))
               for pt in p.findall("point")]
        pts_list.append(pts)
    wood_ref[gi] = pts_list

# Print per-point comparison for elements 0, 2
for ei in [0, 2]:
    ours = our.get(ei, [])
    ref  = wood_ref.get(ei, [])
    n_poly = min(len(ours), len(ref))
    print(f"\n=== element {ei}: {len(ours)} polys ours, {len(ref)} polys wood ===")
    for pi in range(min(4, n_poly)):
        op = ours[pi]
        rp = ref[pi]
        n = min(len(op), len(rp))
        devs = []
        for k in range(n):
            ox,oy,oz = op[k]
            rx,ry,rz = rp[k]
            d = math.sqrt((ox-rx)**2+(oy-ry)**2+(oz-rz)**2)
            devs.append(d)
        max_dev = max(devs) if devs else 0
        print(f"  poly {pi} ({len(op)}pts, max_dev={max_dev:.3f}mm):")
        for k in range(n):
            ox,oy,oz = op[k]
            rx,ry,rz = rp[k]
            dx,dy,dz = ox-rx, oy-ry, oz-rz
            d = math.sqrt(dx**2+dy**2+dz**2)
            if d > 0.01:
                print(f"    pt{k:2d}: our=({ox:.3f},{oy:.3f},{oz:.3f}) wood=({rx:.3f},{ry:.3f},{rz:.3f}) delta=({dx:.3f},{dy:.3f},{dz:.3f}) dist={d:.3f}")
