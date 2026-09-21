# -*- coding: utf-8 -*-
# 28集贴轨 v1 — base=1708.657 (Region 28)，报告已帧证据核验
# Q版插绘段(13-16/17-20)按 7/8/10 集同款留白，卡通课未开
import time, sys, sqlite3, os
from ipaddress import IPv4Address
import reapy_boost
from reapy_boost.tools.network.machines import Host
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))  # 指向本包 pipeline

reapy_boost.connect(Host(IPv4Address("127.0.0.1")))
RPR = reapy_boost.reascript_api
p = reapy_boost.Project()
time.sleep(1)
db = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline", "asset_library.db"))

def q(name):
    r = db.execute("SELECT path FROM assets WHERE name=? LIMIT 1", (name,)).fetchone()
    if r: return r[0]
    r = db.execute("SELECT path FROM assets WHERE name LIKE ? LIMIT 1", (name + '%',)).fetchone()
    if not r: raise RuntimeError(f"库里没有: {name}")
    return r[0]

S = {
    'SRC6':  q("CC-CK Movement Cloth 06"),
    'WOODCR':q("DBDS Impact Wood Small 01"),
    'MANA':  q("MAFDS WHOOSH ARCANE SMALL Mana Wav"),
    'LING3': q("法术 宝物 灵光 3 【声羽拾光】"),
    'WM21':  q("Whoosh Medium 21"),
    'STEAM': q("MBCK PROP Steam Iron Hiss Soft Short"),
    'BITE':  q("CFDS BITE Bill Medium 01"),
    'COUGH': q("MBCK HUMAN Exhale Cough Burst"),
    'STEP3': db.execute("SELECT path FROM assets WHERE name LIKE 'CFCK STEP WOOD%Boots%' LIMIT 1").fetchone()[0],
    'GUST':  q("WHSH_ORGANIC-Wind Base Gust Long_B00M_CMCK"),
}

BASE = 1708.657
CUES = [
    (16, 2.5,  'SRC6',   2.0, "翻书检查",     0.5, 21,  0.5,  None),
    (18, 8.6,  'WOODCR', 0.8, "拍书按堆",     0.3, 0,   0.7,  None),
    (22, 22.3, 'MANA',   1.5, "蓝光聚能",     0.5, 10,  0.6,  None),
    (25, 23.2, 'LING3',  1.5, "馒头蓝焰浮空", 0.5, 10,  0.6,  None),
    (19, 24.4, 'WM21',   1.2, "馒头飘移嗖",   0.4, 4,   0.6,  None),
    (21, 24.8, 'STEAM',  1.5, "蒸汽嘶",       0.5, 0,   0.45, None),
    (17, 26.6, 'BITE',   1.8, "大口咀嚼",     0.3, 0,   0.8,  None),
    (18, 28.3, 'COUGH',  1.5, "咳嗽清嗓",     0.4, 0,   0.6,  None),
    (21, 31.0, 'STEP3',  1.5, "逃跑脚步",     0.4, 10,  0.7,  None),
    (23, 31.5, 'GUST',   1.0, "收黑淡出",     0.8, 30,  0.45, None),
]

dur = dict(db.execute("SELECT path, duration FROM assets").fetchall())
by_fn = {}
for path, d in dur.items():
    by_fn[os.path.basename(path).lower()] = max(by_fn.get(os.path.basename(path).lower(), 0), d or 0)
db.close()

def put(ti, t_local, src, ln, label, fade=None, off=None, vol=None, fadein=None):
    pos = BASE + t_local
    t = p.tracks[ti]
    for it in t.items:
        if abs(it.position - pos) < 0.15:
            try:
                _ = it.takes[0].source.filename
                return None
            except Exception:
                RPR.DeleteTrackMediaItem(t.id, it.id)
    item_id = RPR.AddMediaItemToTrack(t.id)
    take_id = RPR.AddTakeToMediaItem(item_id)
    src_id = RPR.PCM_Source_CreateFromFile(src)
    if not src_id or int(str(src_id).split("0x")[1], 16) == 0:
        return "src失败"
    RPR.SetMediaItemTake_Source(take_id, src_id)
    RPR.SetMediaItemInfo_Value(item_id, "D_POSITION", pos)
    RPR.SetMediaItemInfo_Value(item_id, "D_LENGTH", ln)
    if off is not None: RPR.SetMediaItemTakeInfo_Value(take_id, "D_STARTOFFS", off)
    if fade: RPR.SetMediaItemInfo_Value(item_id, "D_FADEOUTLEN", fade)
    if fadein: RPR.SetMediaItemInfo_Value(item_id, "D_FADEINLEN", fadein)
    RPR.SetMediaItemInfo_Value(item_id, "D_VOL", 1.0)  # 2026-09-11 制作人口径：一律默认音量
    # ⚠️ 旧版此处为 `if vol: ...D_VOL", vol)`（vol 列真值生效），20260916 因照抄致 531 条被调量返工，已中和。
    # CUES 里的 vol 字段仅为兼容保留，落地一律强制 1.0。
    return True

todo = CUES
for rnd in (1, 2):
    todo2 = []
    for cue in todo:
        r = put(cue[0], cue[1], S[cue[2]], cue[3], cue[4], cue[5], cue[6], cue[7], cue[8])
        if r is None: continue
        if r is not True: todo2.append(cue)
    todo = todo2
    if not todo:
        break
    time.sleep(0.6)

# 区间对账（防重跳过会导致计数失真，直接数区间内条目）
print(f"=== 28集区间对账 (1708.657~1741.24) ===", flush=True)
n, badsrc, badoff = 0, 0, 0
for idx in range(14, 27):
    t = p.tracks[idx]
    for it in sorted(t.items, key=lambda x: x.position):
        if BASE - 0.01 <= it.position < BASE + 32.65:
            try:
                fn = os.path.basename(it.takes[0].source.filename)
                d = by_fn.get(fn.lower())
                off = it.takes[0].start_offset
                note = ""
                if d is None: note = "  ⚠️时长未知"
                elif off + it.length > d + 0.05: note = f"  ⚠️越界 off={off:.1f}+{it.length:.1f}>{d:.1f}"; badoff += 1
                print(f"  [{idx}] {it.position-BASE:5.2f}s off={off:5.2f} +{it.length:.2f}  {fn[:40]}{note}", flush=True)
            except Exception:
                print(f"  [{idx}] {it.position-BASE:5.2f}s  !!无源空块!!", flush=True); badsrc += 1
            n += 1
print(f"共 {n} 条（预期 {len(CUES)}），无源 {badsrc}，越界 {badoff}", flush=True)

# 重叠自检
print("\n=== 重叠自检 ===", flush=True)
bad = 0
for idx in range(14, 27):
    t = p.tracks[idx]
    items = sorted(t.items, key=lambda x: x.position)
    for a, b in zip(items, items[1:]):
        if a.position + a.length > b.position + 0.05 and a.position < BASE + 32.65 and b.position < BASE + 32.65:
            print(f"⚠️ [{idx}] {a.position:.2f}s vs {b.position:.2f}s", flush=True); bad += 1
print("重叠通过 ✓" if bad == 0 else f"{bad} 处重叠", flush=True)
