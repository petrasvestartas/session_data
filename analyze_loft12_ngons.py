import sys
import math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.session import Session

data = Session.pb_load(
    r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft12_out.pb')

for mi, mesh in enumerate(data.objects.meshes):
    face_keys = sorted(mesh.face.keys())
    vkey_to_idx = {vk: i for i, vk in enumerate(sorted(mesh.vertex.keys()))}

    dist = {}
    for fk in face_keys:
        n = len(mesh.face[fk])
        dist[n] = dist.get(n, 0) + 1

    with_tri = sum(1 for fk in face_keys if mesh.triangulation.get(fk))
    print(f"\n=== mesh[{mi}] '{mesh.name}' ===")
    print(f"  n-gon dist: {dist}   with_triangulation: {with_tri}/{len(face_keys)}")

    def cross3(a, b, c):
        ax, ay, az = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        bx, by, bz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        return (ay*bz-az*by, az*bx-ax*bz, ax*by-ay*bx)

    for fk in face_keys:
        vks = mesh.face[fk]
        n = len(vks)
        stored = mesh.triangulation.get(fk)
        if n < 5 or stored:
            continue
        pts = [mesh.vertex[vk].position() for vk in vks]
        norms = [cross3(pts[0], pts[i], pts[i+1]) for i in range(1, n-1)]
        ref = norms[0]
        ref_mag = math.sqrt(sum(x*x for x in ref))
        bad = sum(1 for nm in norms
                  if sum(nm[k]*ref[k] for k in range(3)) / (ref_mag + 1e-30) < 0)
        indices = [vkey_to_idx[vk] for vk in vks]
        status = "CONCAVE-FAN-WRONG" if bad else "fan-ok"
        print(f"  fk={fk} n={n} [{status}] verts={indices[:4]}...")
        if bad:
            print(f"    {bad}/{n-2} fan triangles have flipped winding!")
