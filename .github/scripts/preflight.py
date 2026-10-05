"""Preflight checks for the porting job.

Fails fast on the mistake that silently wastes a whole run, and prints the
settings that decide whether the run can succeed at all.

Exit codes: 0 ok, 1 fatal config problem.
"""
import pathlib
import re
import sys

CFG = pathlib.Path("config.ini")
if not CFG.exists():
    print("config.ini not found")
    sys.exit(1)

# 上游读这个文件用 gbk + errors=ignore，这里保持一致
text = CFG.read_text(encoding="gbk", errors="ignore")


def get(key: str, default: str = "") -> str:
    m = re.search(r"^%s\s*=\s*(.*)$" % re.escape(key), text, re.M)
    return (m.group(1).strip() if m else default)


pack_super = get("pack_super", "false").lower()
platform = get("device_platform", "(unset)")
device_size = get("device_size", "(unset)")
fmt = get("format", "erofs").lower()
alg = get("compression", "lz4hc").lower()
level = get("compression_level", "(unset)")
skip_apex = get("is_skip_apex", "false").lower()
old_kernel = get("erofs_old_kernel", "false").lower()

print("---- config.ini summary ----")
for k, v in [
    ("device_platform", platform),
    ("device_size", device_size),
    ("format", fmt),
    ("compression", "%s,%s" % (alg, level)),
    ("pack_super", pack_super),
    ("is_skip_apex", skip_apex),
    ("erofs_old_kernel", old_kernel),
]:
    print("  %-18s %s" % (k, v))

rc = 0
if pack_super != "true":
    print("FATAL: pack_super=false -> super.img is never created, but the workflow needs it.")
    rc = 1

# tools/erofs-utils-cygwin 的老版 mkfs.erofs 只有 lz4/lz4hc/lzma；
# system_ext 在 APEX 同步有变动时会走老版，这时传 zstd/deflate 会直接失败。
if fmt == "erofs" and alg not in ("lz4", "lz4hc", "lzma") and skip_apex != "true" and old_kernel != "true":
    print("WARNING: compression=%s but is_skip_apex!=true -> system_ext may be packed by the "
          "legacy mkfs.erofs (lz4/lz4hc/lzma only) and fail with 'Cannot find a valid "
          "compressor'." % alg)

sys.exit(rc)
