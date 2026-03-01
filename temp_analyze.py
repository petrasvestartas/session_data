import sys
sys.path.insert(0, r'C:\pc\3_code\code_rust\session\session_py\src')
from session_py.objects import Objects

for i in [0, 1, 2, 7, 8, 9, 10]:
    fname = fr'C:\pc\3_code\code_rust\session\session_data\mesh_quad_tri_loft{i}.pb'
    try:
        obj = Objects.pb_load(fname)
        tops = [pl for pl in obj.polylines if pl.name.startswith('top_')]
        bots = [pl for pl in obj.polylines if pl.name.startswith('bot_')]
        print(f"Dataset {i}: {len(tops)} top, {len(bots)} bot polylines")
        for pl in tops[:3]:
            n = len(pl._coords) // 3
            print(f"  {pl.name}: {n} pts")
        for pl in bots[:3]:
            n = len(pl._coords) // 3
            print(f"  {pl.name}: {n} pts")
    except Exception as e:
        print(f"Dataset {i}: ERROR {e}")
