import sys, math
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.session import Session

data = Session.pb_load(r'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft7_out.pb')
meshes = data.objects.meshes

print(f"Total meshes: {len(meshes)}")
print(f"mesh[0] (top): faces={meshes[0].number_of_faces()}")
print(f"mesh[1] (bot): faces={meshes[1].number_of_faces()}")

# Check each panel mesh (indices 2 onwards)
zero_face = []
small_face = []
for i, mesh in enumerate(meshes[2:], start=2):
    verts, faces = mesh.to_vertices_and_faces()
    nv = len(verts)
    nf = len(faces)
    if nf == 0:
        zero_face.append(i-2)
    elif nf <= 2:
        small_face.append((i-2, nf))

print(f"\nPanel meshes with 0 faces: {zero_face}")
print(f"Panel meshes with 1-2 faces: {small_face}")

# Print face count for all panels
print("\nAll panel face counts (panel_idx: n_verts, n_faces):")
for i, mesh in enumerate(meshes[2:]):
    verts, faces = mesh.to_vertices_and_faces()
    if len(faces) <= 2 or i in [0,1,2,34,36,43,54,81]:
        marker = " <-- BAD" if i in [0,1,2,34,36,43,54,81] else ""
        print(f"  panel {i:3d}: verts={len(verts)} faces={len(faces)}{marker}")
