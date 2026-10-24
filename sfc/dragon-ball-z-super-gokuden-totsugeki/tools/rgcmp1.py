"""Compare dialogue id sequences of two lua/scenario.lua batches.

usage: rgcmp1.py dir_a dir_b   (each holds one sub-directory per scenario with ids.txt)

A run that stops early or shows lines in another order is reported; a run that only gets
further in the same number of frames (shorter text prints faster) is not.
"""
import os
import sys


def ids(d):
    p = f"{d}/ids.txt"
    return [l.split()[1] for l in open(p)] if os.path.exists(p) else None


a_dir, b_dir = sys.argv[1:3]
same = longer = 0
for s in sorted(os.listdir(a_dir)):
    a, b = ids(f"{a_dir}/{s}"), ids(f"{b_dir}/{s}")
    if a is None or b is None:
        continue
    k = min(len(a), len(b))
    if a == b:
        same += 1
    elif a[:k] == b[:k] and len(b) > len(a):
        longer += 1
    else:
        i = next((i for i in range(k) if a[i] != b[i]), k)
        print(f"{s}: differs at {i}: {a[i:i + 3]} / {b[i:i + 3]} (lengths {len(a)}/{len(b)})")
print(f"same {same}, b got further {longer}")
