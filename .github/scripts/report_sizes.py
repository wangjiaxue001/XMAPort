"""Report where the space goes in the unpacked source partitions.

Read-only: prints a size breakdown so the log tells us what to slim when
super.img does not fit. Never deletes anything.
"""
import os
import pathlib
import sys

SRC = pathlib.Path("workspace/source_filesystem")
PARTITIONS = ["system", "system_ext", "product", "mi_ext"]
APP_DIRS = ["app", "priv-app", "data-app", "data_app", "overlay", "preload"]
TOP_N = 25
TOP_FILES = 25


def human(n: int) -> str:
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if n < 1024 or unit == "GiB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0
    return str(n)


def dir_size(path: str) -> int:
    total = 0
    for base, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(base, f)
            try:
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def top_children(path: pathlib.Path, n: int):
    out = []
    if not path.is_dir():
        return out
    for child in sorted(path.iterdir()):
        try:
            if child.is_dir() and not child.is_symlink():
                out.append((dir_size(str(child)), child.name))
            elif child.is_file():
                out.append((child.stat().st_size, child.name))
        except OSError:
            pass
    out.sort(reverse=True)
    return out[:n]


def biggest_files(root: pathlib.Path, n: int):
    out = []
    for base, _dirs, files in os.walk(str(root)):
        for f in files:
            fp = os.path.join(base, f)
            try:
                if not os.path.islink(fp):
                    out.append((os.path.getsize(fp), os.path.relpath(fp, str(root))))
            except OSError:
                pass
    out.sort(reverse=True)
    return out[:n]


if not SRC.is_dir():
    sys.exit("no %s (did the unpack step run?)" % SRC)

print("========== source partition sizes ==========")
total_all = 0
for p in PARTITIONS:
    d = SRC / p
    if d.is_dir():
        s = dir_size(str(d))
        total_all += s
        print("  %-12s %s" % (p, human(s)))
    else:
        print("  %-12s (missing)" % p)
print("  %-12s %s" % ("TOTAL", human(total_all)))

for p in PARTITIONS:
    d = SRC / p
    if not d.is_dir():
        continue
    print("\n========== %s: top level ==========" % p)
    for size, name in top_children(d, TOP_N):
        print("  %12s  %s" % (human(size), name))

    for sub in APP_DIRS:
        sd = d / sub
        if sd.is_dir():
            print("\n---------- %s/%s ----------" % (p, sub))
            for size, name in top_children(sd, TOP_N):
                print("  %12s  %s" % (human(size), name))

print("\n========== biggest individual files ==========")
for size, rel in biggest_files(SRC, TOP_FILES):
    print("  %12s  %s" % (human(size), rel))
