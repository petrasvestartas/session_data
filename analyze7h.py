import sys
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.session import Session

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7_out.pb'
data = Session.pb_load(fname)
meshes = list(data.objects.meshes)

print(f"Total meshes: {len(meshes)}")

FAIL_IDX = [0, 25, 108]
for i in FAIL_IDX:
    if i >= len(meshes):
        print(f"mesh[{i}]: OUT OF RANGE")
        continue
    obj = meshes[i]
    face_keys = sorted(obj.face.keys())
    n_faces = len(face_keys)
    n_with_tri = sum(1 for fk in face_keys if obj.triangulation.get(fk))
    n_tri_total = sum(len(obj.triangulation.get(fk, [])) for fk in face_keys)
    face_sizes = sorted(set(len(obj.face[fk]) for fk in face_keys))
    print(f"\nmesh[{i}]: faces={n_faces} face_sizes={face_sizes} "
          f"with_triangulation={n_with_tri} total_tris={n_tri_total}")
    for fk in face_keys[:5]:
        tri = obj.triangulation.get(fk)
        print(f"  face {fk}: n={len(obj.face[fk])} tri={'None' if tri is None else len(tri)}")
