# -*- coding: utf-8 -*-
# 26集 off 验证 + 全工程 offset 越界审计（可续跑）
import time, sys, sqlite3, os
from ipaddress import IPv4Address
import reapy_boost
from reapy_boost.tools.network.machines import Host

reapy_boost.connect(Host(IPv4Address("127.0.0.1")))
RPR = reapy_boost.reascript_api
p = reapy_boost.Project()
time.sleep(1)
db = sqlite3.connect(r"C:/Users/Administrator/Workspace/2026-08-21-14-44-13/reaper-foley-pipeline/index/asset_library.db")
dur = dict(db.execute("SELECT path, duration FROM assets").fetchall())
# 文件名 -> 源长（可能同名不同目录，取最大时长近似）
by_fn = {}
for path, d in dur.items():
    fn = os.path.basename(path).lower()
    by_fn[fn] = max(by_fn.get(fn, 0), d or 0)
db.close()

BASE = 1606.99

def dur_of(fn):
    return by_fn.get(os.path.basename(fn).lower())

print("=== 26集 22条 off 验证 ===", flush=True)
for idx in range(14, 27):
    t = p.tracks[idx]
    for it in sorted(t.items, key=lambda x: x.position):
        if BASE - 0.01 <= it.position < BASE + 58.2:
            try:
                off = it.takes[0].start_offset
                fn = os.path.basename(it.takes[0].source.filename)
                d = dur_of(fn)
                flag = "" if (d is None or off + it.length <= d + 0.05) else "  ⚠️越界"
                print(f"  [{idx}] {it.position-BASE:6.2f}s off={off:5.2f} len={it.length:.2f} src={d} {fn[:34]}{flag}", flush=True)
            except Exception as e:
                print(f"  [{idx}] {it.position-BASE:6.2f}s 读取失败 {e}", flush=True)

print("\n=== 全工程 offset 越界审计 (track 14~26) ===", flush=True)
SKIP = set()  # 上次崩溃位置，续跑时填 (track_idx, round(pos,2))
if len(sys.argv) > 1:
    for tok in sys.argv[1].split(","):
        ti, po = tok.split(":")
        SKIP.add((int(ti), float(po)))
viol = 0
scanned = 0
crashed_at = None
for idx in range(14, 27):
    t = p.tracks[idx]
    items = sorted(t.items, key=lambda x: x.position)
    for it in items:
        if (idx, round(it.position, 2)) in SKIP:
            print(f"  -- 跳过 [{idx}] {it.position:.2f}", flush=True)
            continue
        scanned += 1
        try:
            fn = it.takes[0].source.filename
        except Exception:
            print(f"⚠️ [{idx}] {it.position:.2f}s 无源空块", flush=True)
            viol += 1
            continue
        off = it.takes[0].start_offset
        d = dur_of(fn)
        if d is not None and off + it.length > d + 0.05:
            print(f"⚠️ [{idx}] {it.position:.2f}s off={off:.2f}+len={it.length:.2f} > {d:.2f}  {os.path.basename(fn)[:40]}", flush=True)
            viol += 1
        # 每 50 条 flush 一次进度
        if scanned % 50 == 0:
            print(f"  ...已扫 {scanned}", flush=True)
    print(f"  track {idx} 完成 ({len(items)} items)", flush=True)

print(f"\n扫描 {scanned} 条，越界/空块 {viol} 条", flush=True)
