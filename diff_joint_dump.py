#!/usr/bin/env python3
"""Diff wood vs session joint dumps by (v0, v1, f0, f1) keys.

Usage: python diff_joint_dump.py <name>
  Reads wood_dump_<name>.txt and sess_dump_<name>.txt.
  Prints: joints only-in-wood, only-in-session, and key diffs.
"""
import re
import sys
from pathlib import Path


JOINT_RE = re.compile(
    r"^joint (?P<idx>\d+) type=(?P<type>-?\d+) v0=(?P<v0>-?\d+) v1=(?P<v1>-?\d+) "
    r"f0_0=(?P<f00>-?\d+) f1_0=(?P<f10>-?\d+)"
)


def load_joints(path):
    """Returns: {(v0, v1, f00, f10): (idx, type, full_block_as_str)}."""
    out = {}
    cur_key = None
    cur_idx = None
    cur_type = None
    cur_lines = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = JOINT_RE.match(line)
            if m:
                if cur_key is not None:
                    out[cur_key] = (cur_idx, cur_type, "".join(cur_lines))
                cur_key = (
                    int(m.group("v0")),
                    int(m.group("v1")),
                    int(m.group("f00")),
                    int(m.group("f10")),
                )
                cur_idx = int(m.group("idx"))
                cur_type = int(m.group("type"))
                cur_lines = [line]
            else:
                cur_lines.append(line)
    if cur_key is not None:
        out[cur_key] = (cur_idx, cur_type, "".join(cur_lines))
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: diff_joint_dump.py <name>")
        sys.exit(2)
    name = sys.argv[1]
    data_dir = Path(__file__).resolve().parent
    wood_path = data_dir / f"wood_dump_{name}.txt"
    sess_path = data_dir / f"sess_dump_{name}.txt"
    if not wood_path.exists():
        print(f"missing: {wood_path}")
        sys.exit(1)
    if not sess_path.exists():
        print(f"missing: {sess_path}")
        sys.exit(1)
    wood = load_joints(wood_path)
    sess = load_joints(sess_path)
    print(f"wood joints: {len(wood)}")
    print(f"session joints: {len(sess)}")

    wood_keys = set(wood.keys())
    sess_keys = set(sess.keys())
    only_wood = wood_keys - sess_keys
    only_sess = sess_keys - wood_keys
    shared = wood_keys & sess_keys
    print(f"  shared: {len(shared)}")
    print(f"  only wood: {len(only_wood)}")
    print(f"  only session: {len(only_sess)}")

    if only_wood:
        print("\n== ONLY IN WOOD ==")
        for k in sorted(only_wood)[:50]:
            idx, jt, _ = wood[k]
            print(f"  v0={k[0]} v1={k[1]} f0={k[2]} f1={k[3]} | wood_idx={idx} type={jt}")

    if only_sess:
        print("\n== ONLY IN SESSION ==")
        for k in sorted(only_sess)[:50]:
            idx, jt, _ = sess[k]
            print(f"  v0={k[0]} v1={k[1]} f0={k[2]} f1={k[3]} | sess_idx={idx} type={jt}")


if __name__ == "__main__":
    main()
