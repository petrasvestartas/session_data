import sys
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.session import Session

fname = r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7_out.pb'
data = Session.pb_load(fname)
meshes = list(data.objects.meshes)

print(f"Total meshes: {len(meshes)}")

# Check all orig_panels (indices 2..N+1) for their face structure
# and triangulation coverage
n_panels = (len(meshes) - 2) // 2
print(f"Approx panels: {n_panels}")

issues = []
for i in range(2, 2 + n_panels):
    obj = meshes[i]
    face_keys = sorted(obj.face.keys())
    face_sizes = [len(obj.face[fk]) for fk in face_keys]
    n_ngon = sum(1 for s in face_sizes if s >= 5)  # n-gon faces (n>=5)
    n_ngon_with_tri = sum(1 for fk in face_keys
                          if len(obj.face[fk]) >= 5 and obj.triangulation.get(fk))
    if n_ngon > 0 and n_ngon_with_tri < n_ngon:
        issues.append((i, n_ngon, n_ngon_with_tri, sorted(set(face_sizes))))

print(f"\nOrig panels missing ngon CDT (n_ngon > n_with_tri):")
for (i, ng, nwt, fs) in issues[:20]:
    print(f"  mesh[{i}]: n_ngon={ng} with_CDT={nwt} face_sizes={fs}")

if not issues:
    print("  None! All n-gon faces in orig_panels have CDT stored.")

# Also check: mesh[0] top_mesh - how many faces have CDT now?
obj0 = meshes[0]
fks0 = sorted(obj0.face.keys())
n_with = sum(1 for fk in fks0 if obj0.triangulation.get(fk))
n_without = len(fks0) - n_with
print(f"\ntop_mesh: {len(fks0)} faces, {n_with} with CDT, {n_without} without CDT")
if n_without > 0:
    print("  Faces without CDT:")
    for fk in fks0:
        if not obj0.triangulation.get(fk):
            print(f"    face {fk}: n={len(obj0.face[fk])}")
