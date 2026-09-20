# -*- coding: utf-8 -*-
# 分轨导出 v4 — solo-loop + 41824 无对话框渲染 + 完整性等待
# 每轨: solo → 渲染 → 轮询文件大小到 920MB± 且 5s 稳定 → 下一轨；短文件自动重试
import os, time, json
from ipaddress import IPv4Address
import reapy_boost
from reapy_boost.tools.network.machines import Host

reapy_boost.connect(Host(IPv4Address("127.0.0.1")))
RPR = reapy_boost.reascript_api
p = reapy_boost.Project()
time.sleep(1)

OUT = r"C:\Users\Administrator\Desktop\3D颠佬-分轨导出_48k24b"
os.makedirs(OUT, exist_ok=True)
states = json.load(open(r"C:/Users/Administrator/Workspace/2026-08-24-10-46-09/check/fader_backup_20260831.json"))
EXPECT = 919_000_000  # 3197s * 288000B/s ≈ 920.7MB，留余量

# 清掉 v3 的残件
for f in os.listdir(OUT):
    if f.endswith(".wav"):
        try: os.remove(os.path.join(OUT, f))
        except Exception: pass

# 公共渲染配置
RPR.GetSetProjectInfo_String(0, "RENDER_FORMAT", "ZXZhdxgAAAA=", True)  # 24bit WAV
RPR.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, True)    # master mix（solo 隔离出单轨）
RPR.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, True)  # entire project
RPR.GetSetProjectInfo(0, "RENDER_SRATE", 48000, True)
RPR.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, True)
RPR.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, True)
RPR.GetSetProjectInfo(0, "RENDER_DITHER", 0, True)
RPR.GetSetProjectInfo(0, "RENDER_ADDTOPROJ", 0, True)
RPR.GetSetProjectInfo(0, "RENDER_NORMALIZE", 0, True)
RPR.GetSetProjectInfo(0, "RENDER_RESAMPLE", 3, True)
RPR.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, True)

def zero_all():
    for t in p.tracks:
        RPR.SetMediaTrackInfo_Value(t.id, "D_VOL", 1.0)
        RPR.SetMediaTrackInfo_Value(t.id, "B_MUTE", 0)
        RPR.SetMediaTrackInfo_Value(t.id, "I_SOLO", 0)

def render_and_wait(path, timeout=300):
    """触发渲染并等待文件写满稳定。返回 (final_size, ok)"""
    RPR.Main_OnCommand(41824, 0)  # Render project to disk (no dialog)
    stable, last = 0, -1
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(4)
        sz = os.path.getsize(path) if os.path.exists(path) else 0
        if sz >= EXPECT:
            return sz, True
        if sz == last and sz > 0:
            stable += 1
            if stable >= 2:
                return sz, False  # 稳定但没写满 → 短渲染
        else:
            stable = 0
        last = sz
    return (os.path.getsize(path) if os.path.exists(path) else 0), False

results = []
for i in range(14, 29):
    t = p.tracks[i]
    try: name = t.name
    except Exception: name = f"track{i}"
    fp = os.path.join(OUT, name + ".wav")
    ok, attempt_log = False, []
    for attempt in (1, 2, 3):
        zero_all()
        for j, tt in enumerate(p.tracks):
            RPR.SetMediaTrackInfo_Value(tt.id, "I_SOLO", 1 if j == i else 0)
        RPR.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, True)
        if os.path.exists(fp):
            try: os.remove(fp)
            except Exception: pass
        time.sleep(0.5)
        sz, ok = render_and_wait(fp)
        attempt_log.append(f"#{attempt}={sz/1e6:.0f}MB{'✓' if ok else '✗'}")
        if ok: break
        time.sleep(1.5)
    results.append((i, name, sz if ok else 0, ok, "|".join(attempt_log)))
    print(f"[{i}] {name}: {'✓ ' if ok else '✗ '}{sz/1e6:.0f}MB  ({'|'.join(attempt_log)})", flush=True)

# 恢复推子/静音/独奏
for s in states:
    t = p.tracks[s["i"]]
    RPR.SetMediaTrackInfo_Value(t.id, "D_VOL", s["vol"])
    RPR.SetMediaTrackInfo_Value(t.id, "B_MUTE", s["mute"])
    RPR.SetMediaTrackInfo_Value(t.id, "I_SOLO", s["solo"])
    RPR.SetMediaTrackInfo_Value(t.id, "I_SELECTED", 0)
diff = 0
for s in states:
    t = p.tracks[s["i"]]
    r = RPR.GetTrackUIVolPan(t.id, 0.0, 0.0)
    if abs(float(r[2]) - s["vol"]) > 0.0005: diff += 1
ok_n = sum(1 for r in results if r[3])
print(f"\n完成 {ok_n}/15 轨；推子恢复差异 {diff}", flush=True)
if ok_n < 15:
    print("失败轨:", [(r[1], r[4]) for r in results if not r[3]], flush=True)
