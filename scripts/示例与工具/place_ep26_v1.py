# -*- coding: utf-8 -*-
# 26集贴轨 v1 — base=1606.99 (Region 26)，报告已帧证据核验
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
    'SLAP':  q("CC-DS Slap Bright Hard 01"),
    'FIRE':  q("CECK FIRE Whoosh Fireball"),
    'MAYHEM':q("Matter Mayhem - Wood-Small barrack crash-02"),
    'DRONE': q("CDDS SCARY DRONE LOW Machinery"),
    'TELE':  q("MADS Teleport Light"),
    'GUST':  q("WHSH_ORGANIC-Wind Base Gust Long_B00M_CMCK"),
    'ZHENFA':q("法术 阵法 开启 【声羽拾光】"),
    'RING':  q("玄幻法器 无定飞环 振动 【声羽拾光】"),
    'SKILL': q("法术 技能起手 【声羽拾光】"),
    'LING1': q("法术 宝物 灵光 1 【声羽拾光】"),
    'LING2': q("法术 宝物 灵光 2 【声羽拾光】"),
    'LING3': q("法术 宝物 灵光 3 【声羽拾光】"),
    'BGHARD':q("CC-DS Bodygrab Cloth Hard"),
}

BASE = 1606.99
CUES = [
    (16, 0.5,  'SRC6',   1.0, "翻书页",        0.4, 6.4, 0.5, None),
    (18, 3.3,  'WOODCR', 0.9, "合书按桌",      0.3, 6,   0.7, None),
    (19, 6.3,  'CRYST',  0.7, "笔尖红光(弱)",   0.3, 30,  0.5, None),
    (22, 6.8,  'MANA',   1.5, "画符魔力滋滋",   0.5, 15,  0.5, None),
    (19, 10.4, 'SLAP',   0.6, "弹指清脆",      0.2, 0,   0.8, None),
    (20, 13.2, 'FIRE',   2.0, "符纸自燃爆燃",   0.7, 0,   1.0, None),
    (20, 18.4, 'MAYHEM', 1.8, "符爆黑烟轰响",   0.8, 0,   1.1, None),
    (21, 19.6, 'DRONE',  2.5, "余烟轰隆(弱)",   1.2, 30,  0.5, None),
    (18, 21.0, 'WOODCR', 0.8, "焦笔落桌",      0.3, 8,   0.6, None),
    (16, 22.4, 'SRC6',   1.0, "翻焦书",        0.4, 16.4,0.5, None),
    (25, 38.5, 'LING1',  1.5, "复制符页发光",   0.5, 15,  0.7, None),
    (23, 42.2, 'TELE',   2.0, "白发现身凝聚",   1.0, 0,   0.8, 0.8),
    (25, 42.7, 'LING3',  2.0, "金色粒子升腾",   0.6, 15,  0.7, None),
    (22, 44.2, 'MANA',   1.5, "绿旋涡聚能",    0.5, 18,  0.8, None),
    (23, 45.4, 'GUST',   1.5, "净化扫过",      0.6, 25,  0.7, None),
    (20, 48.3, 'ZHENFA', 2.0, "金色星阵展开",   0.7, 0,   0.9, None),
    (24, 48.2, 'RING',   0.8, "星阵微光嗡",    0.3, 2.5, 0.5, None),
    (20, 53.3, 'SKILL',  1.5, "掌心聚能",      0.5, 15,  0.8, None),
    (25, 53.8, 'LING2',  1.5, "金光光团",      0.5, 15,  0.7, None),
    (18, 55.2, 'BGHARD', 0.5, "提笔手部轻响",   0.2, 3.0, 0.4, None),
    (19, 56.3, 'CRYST',  0.7, "尾段画符滋滋(同款)",0.3, 22, 0.5, None),
    (24, 57.4, 'RING',   0.7, "收笔亮音",      0.3, 5.0, 0.6, None),
]

dur = dict(db.execute("SELECT path, duration FROM assets").fetchall())
placed, failed = [], []

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
    RPR.GetSetMediaItemTakeInfo_String(take_id, "P_NAME", os.path.splitext(os.path.basename(src))[0], True)  # 条目名=源文件名 stem（04号文档口径；不设则画面里 item 无标签）
    # ⚠️ 旧版此处为 `if vol: ...D_VOL", vol)`（vol 列真值生效），20260916 因照抄致 531 条被调量返工，已中和。
    # CUES 里的 vol 字段仅为兼容保留，落地一律强制 1.0。
    # 立即验证源
    try:
        fn = RPR.GetActiveTake(item_id)  # 占位，防未用
    except Exception:
        pass
    ok = False
    for tk_i in range(RPR.CountTakes(item_id)):
        tk = RPR.GetTake(item_id, tk_i)
        s = RPR.GetMediaItemTake_Source(tk)
        if s and int(str(s).split("0x")[1], 16) != 0:
            ok = True
    if not ok:
        RPR.DeleteTrackMediaItem(t.id, item_id)
        return "source丢失"
    placed.append((pos, ti, label, ln))
    return True

todo = CUES
for rnd in (1, 2):
    todo2 = []
    for cue in todo:
        ti, t_local, skey, ln, label = cue[0], cue[1], S[cue[2]], cue[3], cue[4]
        fade, off, vol, fi = cue[5], cue[6], cue[7], cue[8]
        r = put(ti, t_local, S[cue[2]], ln, label, fade, off, vol, fi)
        if r is None: continue
        if r is not True: todo2.append(cue)
    todo = todo2
    if not todo:
        break
    time.sleep(0.6)

print(f"=== 26集贴轨 {len(placed)}/22 条 ===")
if todo: print("失败:", [(c[4],) for c in todo])

# 自检1: 重叠
print("\n=== 重叠自检 ===")
bad = 0
for idx in range(14, 27):
    t = p.tracks[idx]
    items = sorted(t.items, key=lambda x: x.position)
    for a, b in zip(items, items[1:]):
        if a.position + a.length > b.position + 0.05:
            print(f"⚠️ [{idx}] {a.position:.2f}s vs {b.position:.2f}s"); bad += 1
print("重叠通过 ✓" if bad == 0 else f"{bad} 处重叠")

# 自检2: 26集区间 item 对账
print("\n=== 26集区间对账 (1606.99~1665.12) ===")
n = 0
for idx in range(14, 27):
    t = p.tracks[idx]
    for it in sorted(t.items, key=lambda x: x.position):
        if BASE - 0.01 <= it.position < BASE + 58.2:
            try:
                fn = os.path.basename(it.takes[0].source.filename)
            except Exception:
                fn = "!!无源!!"
            print(f"  [{idx}] {it.position-BASE:6.2f}s +{it.length:.2f}  {fn[:46]}")
            n += 1
print(f"共 {n} 条")

# 自检3: 全工程 offset 越界审计 (track 14~26)
print("\n=== 全工程 offset 越界审计 ===")
viol = 0
for idx in range(14, 27):
    t = p.tracks[idx]
    for it in t.items:
        try:
            fn = it.takes[0].source.filename
        except Exception:
            print(f"⚠️ [{idx}] {it.position:.2f}s 无源空块"); viol += 1; continue
        key = fn.replace("/", "\\").lower()
        d = None
        for path, du in dur.items():
            if path.lower().endswith(key) or path.lower() == key:
                d = du; break
        if d is None: continue
        off = RPR.GetMediaItemTakeInfo_Value(it.takes[0].id, "D_STARTOFFS")
        if off + it.length > d + 0.05:
            print(f"⚠️ [{idx}] {it.position:.2f}s off={off:.2f}+len={it.length:.2f} > 源长{d:.2f}  {os.path.basename(fn)[:40]}")
            viol += 1
print("offset 全部在界内 ✓" if viol == 0 else f"{viol} 条越界")
db.close()
