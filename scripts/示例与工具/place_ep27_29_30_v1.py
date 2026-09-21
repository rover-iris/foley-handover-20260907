# -*- coding: utf-8 -*-
# 27/29/30 集三连贴 v1 — 报告均已帧证据核验
# 27: base=1665.115 (43.54s) | 29: base=1741.24 (58.21s) | 30: base=1799.448 (38.25s)
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
    'CRYST': q("DSGNMisc_TAIL LIGHT-Crystal Clear_B00M_CXDS_A"),
    'MANA':  q("MAFDS WHOOSH ARCANE SMALL Mana Wav"),
    'WM21':  q("Whoosh Medium 21"),
    'RUSH':  q("WHSH_CINEMATIC ORGANIC FAST-Rush_B00M_CMDS"),
    'DRONE': q("CDDS SCARY DRONE LOW Machinery"),
    'LING1': q("法术 宝物 灵光 1 【声羽拾光】"),
    'LING2': q("法术 宝物 灵光 2 【声羽拾光】"),
    'LING3': q("法术 宝物 灵光 3 【声羽拾光】"),
    'GUST':  q("WHSH_ORGANIC-Wind Base Gust Long_B00M_CMCK"),
    'STEP3': db.execute("SELECT path FROM assets WHERE name LIKE 'CFCK STEP WOOD%Boots%' LIMIT 1").fetchone()[0],
    'PAPER': q("CFCK WINGS Constant Tiny Paper Bag Rustle"),
    'BFALL': q("CC-DS Body Fall Generic Soft 02"),
    'BGHARD':q("CC-DS Bodygrab Cloth Hard"),
    'SKILL': q("法术 技能起手 【声羽拾光】"),
    'BITE':  q("CFDS BITE Bill Medium 01"),
    'TELE':  q("MADS Teleport Light"),
    'PUNCH': q("CC-DS Punch Cinematic 01"),
    'DRAW':  q("剑魂 draw sword 拔剑 【声羽拾光】"),
    'FJ':    q("玄幻法器 飞剑 运动 【声羽拾光】"),
    'WIND':  q("QP02 0139 Wind modern light variable wires"),
    'ZHENFA':q("法术 阵法 开启 【声羽拾光】"),
    'MAYHEM':q("Matter Mayhem - Wood-Small barrack crash-02"),
    'STEAM': q("MBCK PROP Steam Iron Hiss Soft Short"),
    'GLOW':  q("法术 打击 结界  结界发出光晕 【声羽拾光】"),
    'EXHALE':q("MBCK HUMAN Exhale Burst"),
}

EPS = {
27: (1665.115, 43.54, [
    (18, 0.4,  'WOODCR', 0.6, "搁笔轻响",     0.2, 4,   0.5, None),
    (16, 1.4,  'SRC6',   1.0, "拿纸摩擦",     0.4, 26,  0.5, None),
    (19, 3.2,  'CRYST',  0.7, "符纸激活亮音",  0.3, 40,  0.8, None),
    (25, 9.2,  'WM21',   1.2, "符纸破空飞空",  0.4, 10,  0.8, None),
    (20, 10.8, 'RUSH',   1.0, "金色光束横扫",  0.4, 2,   0.9, None),
    (22, 12.0, 'DRONE',  1.5, "黑屏转场低鸣",  0.8, 60,  0.4, None),
    (16, 13.3, 'SRC6',   1.5, "笔尖画纸沙沙",  0.5, 11,  0.5, None),
    (25, 13.6, 'LING1',  2.0, "符堆金光持续",  0.6, 20,  0.6, None),
    (20, 22.4, 'PAPER',  1.5, "纸人抬书起势",  0.4, 5,   0.6, None),
    (18, 24.0, 'WOODCR', 0.7, "青年扶书碰桌",  0.3, 2,   0.5, None),
    (22, 25.3, 'MANA',   1.5, "白发聚能嗡鸣",  0.5, 5,   0.7, None),
    (25, 27.0, 'LING2',  1.5, "挥臂金色光流",  0.5, 25,  0.8, None),
    (20, 28.4, 'PAPER',  1.2, "纸人搬书窸窣",  0.4, 12,  0.5, None),
    (25, 29.3, 'LING3',  1.5, "纸人消散轻音",  0.8, 22,  0.5, None),
    (22, 30.3, 'GUST',   2.0, "巨影化雾消散",  1.0, 20,  0.6, None),
    (21, 36.3, 'DRONE',  3.0, "红雾弥漫涌动",  1.2, 80,  0.5, None),
    (21, 40.3, 'STEP3',  1.5, "老者沉重脚步",  0.4, 25,  0.7, None),
]),
29: (1741.24, 58.21, [
    (19, 0.15, 'RUSH',   1.0, "破窗跃入破空",  0.4, 5,   0.9, None),
    (18, 0.85, 'BFALL',  0.8, "落地闷响",     0.3, 0,   0.7, None),
    (18, 4.3,  'WOODCR', 0.9, "合书",        0.3, 3,   0.7, None),
    (16, 6.0,  'SRC6',   1.0, "翻书",        0.4, 2,   0.5, None),
    (17, 7.5,  'BGHARD', 0.6, "取纸人轻响",   0.2, 1,   0.4, None),
    (25, 9.3,  'LING3',  2.0, "纸人悬浮微光",  0.6, 28,  0.5, None),
    (19, 15.2, 'CRYST',  0.7, "符文点亮叮",   0.3, 45,  0.8, None),
    (22, 21.2, 'SKILL',  1.5, "掌心聚能凝球",  0.5, 10,  0.8, None),
    (20, 23.2, 'MANA',   1.5, "水镜显像嗡鸣",  0.5, 2,   0.6, None),
    (17, 26.5, 'BITE',   2.0, "啃馒头咀嚼",   0.4, 3,   0.7, None),
    (22, 32.3, 'MANA',   1.5, "水镜收敛消散",  0.8, 12,  0.5, None),
    (18, 43.0, 'WOODCR', 0.6, "纸人放桌轻响",  0.2, 8,   0.4, None),
    (23, 48.2, 'TELE',   2.0, "蓝光化虚传送",  0.8, 3,   0.8, 0.5),
    (25, 48.7, 'LING2',  1.5, "蓝光粒子未散",  0.6, 35,  0.5, None),
    (17, 50.8, 'PUNCH',  1.0, "握拳抵窗闷响",  0.3, 0,   0.7, None),
    (20, 56.9, 'DRAW',   0.7, "剑鸣出鞘",     0.2, 0,   0.9, None),
    (24, 57.6, 'FJ',     0.6, "御剑破空起飞",  0.2, 10,  0.9, None),
]),
30: (1799.448, 38.25, [
    (17, 2.2,  'BITE',   2.0, "咬馒头+咀嚼",  0.4, 4,   0.7, None),
    (17, 5.5,  'BITE',   1.2, "再咬馒头",     0.3, 0,   0.7, None),
    (23, 9.0,  'WIND',   2.0, "高处风声",     0.6, 30,  0.5, None),
    (16, 14.3, 'SRC6',   1.5, "纸人挪动窸窣",  0.4, 8,   0.5, None),
    (16, 16.3, 'SRC6',   1.0, "纸人扶笔",     0.3, 18,  0.4, None),
    (23, 19.0, 'WIND',   2.0, "空镜风声",     0.6, 60,  0.4, None),
    (21, 19.8, 'DRONE',  2.5, "邪气低吼汇聚",  0.8, 110, 0.6, None),
    (20, 21.2, 'ZHENFA', 2.0, "法轮屏障嗡鸣",  0.6, 8,   0.8, None),
    (19, 22.3, 'MAYHEM', 1.0, "黑烟撞击闷响",  0.3, 2,   0.8, None),
    (21, 24.2, 'STEAM',  1.5, "黑烟爬行嘶嘶",  0.5, 4,   0.5, None),
    (19, 26.2, 'BGHARD', 0.8, "黑烟缠腕",     0.3, 1,   0.6, None),
    (24, 28.0, 'CRYST',  0.9, "双目金光铮鸣",  0.3, 50,  0.9, None),
    (20, 29.1, 'GLOW',   1.5, "符文金环缚烟",  0.5, 0,   0.8, None),
    (25, 30.0, 'LING3',  1.5, "净化消散",     0.8, 5,   0.5, None),
    (17, 31.2, 'EXHALE', 1.5, "抚胸喘息",     0.4, 2,   0.6, None),
    (20, 37.0, 'ZHENFA', 1.2, "法轮持续嗡鸣",  0.4, 16,  0.6, None),
]),
}

def put(ti, t_local, src, ln, label, fade=None, off=None, vol=None, fadein=None):
    pos = base + t_local
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

todo_all = []
for ep, (base, eplen, cues) in EPS.items():
    for c in cues:
        todo_all.append((ep, base, eplen) + tuple(c))

for rnd in (1, 2):
    todo2 = []
    for item in todo_all:
        ep, base, eplen = item[0], item[1], item[2]
        ti, t_local, skey, ln, label = item[3], item[4], item[5], item[6], item[7]
        r = put(ti, t_local, S[skey], ln, label, item[8], item[9], item[10], item[11])
        if r is None: continue
        if r is not True: todo2.append(item)
    todo_all = todo2
    if not todo_all:
        break
    time.sleep(0.8)

dur = dict(db.execute("SELECT path, duration FROM assets").fetchall())
by_fn = {}
for path, d in dur.items():
    by_fn[os.path.basename(path).lower()] = max(by_fn.get(os.path.basename(path).lower(), 0), d or 0)
db.close()

for ep, (base, eplen, cues) in EPS.items():
    print(f"\n=== ep{ep} 区间对账 ({base}~{base+eplen}) 预期 {len(cues)} 条 ===", flush=True)
    n = bad = 0
    for idx in range(14, 27):
        t = p.tracks[idx]
        for it in sorted(t.items, key=lambda x: x.position):
            if base - 0.01 <= it.position < base + eplen + 0.1:
                try:
                    fn = os.path.basename(it.takes[0].source.filename)
                    d = by_fn.get(fn.lower())
                    off = it.takes[0].start_offset
                    warn = ""
                    if d is not None and off + it.length > d + 0.05:
                        warn = f"  ⚠️越界 off={off:.1f}+{it.length:.1f}>{d:.1f}"; bad += 1
                    print(f"  [{idx}] {it.position-base:6.2f}s off={off:5.2f} +{it.length:.2f} {fn[:38]}{warn}", flush=True)
                except Exception:
                    print(f"  [{idx}] {it.position-base:6.2f}s !!无源!!", flush=True); bad += 1
                n += 1
    print(f"  实际 {n} 条, 异常 {bad}", flush=True)

print("\n=== 三集重叠自检 ===", flush=True)
bad = 0
for ep, (base, eplen, cues) in EPS.items():
    for idx in range(14, 27):
        t = p.tracks[idx]
        items = sorted([it for it in t.items if base-0.1 <= it.position < base+eplen+0.2], key=lambda x: x.position)
        for a, b in zip(items, items[1:]):
            if a.position + a.length > b.position + 0.05:
                print(f"⚠️ ep{ep} [{idx}] {a.position-base:.2f} vs {b.position-base:.2f}", flush=True); bad += 1
print("重叠通过 ✓" if bad == 0 else f"{bad} 处重叠", flush=True)
