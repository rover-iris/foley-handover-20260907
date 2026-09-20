# -*- coding: utf-8 -*-
# 渲染格式试条 — 验证 48k/24bit WAV 配置
import os, time, base64, subprocess
from ipaddress import IPv4Address
import reapy_boost
from reapy_boost.tools.network.machines import Host

reapy_boost.connect(Host(IPv4Address("127.0.0.1")))
RPR = reapy_boost.reascript_api
p = reapy_boost.Project()
time.sleep(1)

TMP = r"C:\Users\Administrator\Workspace\2026-08-24-10-46-09\check\fmt_test"
os.makedirs(TMP, exist_ok=True)
ffprobe = r"C:\Users\Administrator\ffmpeg\ffprobe.exe"

# 先读当前渲染格式
cur = RPR.GetSetProjectInfo_String(0, "RENDER_FORMAT", "", False)
print("当前 RENDER_FORMAT:", cur)

candidates = ["ZXZhdxgAAAA=", "ZXZhdxAYAAA="]
ok = None
for cand in candidates:
    wav = os.path.join(TMP, "fmttest.wav")
    if os.path.exists(wav): os.remove(wav)
    RPR.GetSetProjectInfo_String(0, "RENDER_FORMAT", cand, True)
    RPR.GetSetProjectInfo(0, "RENDER_FILE", 0, True)  # 无效占位
    RPR.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, True)   # master mix
    RPR.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, True) # custom
    RPR.GetSetProjectInfo(0, "RENDER_STARTPOS", 0, True)
    RPR.GetSetProjectInfo(0, "RENDER_ENDPOS", 0.5, True)
    RPR.GetSetProjectInfo(0, "RENDER_SRATE", 48000, True)
    RPR.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, True)
    RPR.GetSetProjectInfo(0, "RENDER_DITHER", 0, True)
    RPR.GetSetProjectInfo(0, "RENDER_ADDTOPROJ", 0, True)
    RPR.GetSetProjectInfo(0, "RENDER_NORMALIZE", 0, True)
    RPR.GetSetProjectInfo_String(0, "RENDER_FILE", TMP, True)
    RPR.GetSetProjectInfo_String(0, "RENDER_PATTERN", "fmttest", True)
    RPR.Main_OnCommand(42230, 0)  # render recent settings auto-close
    time.sleep(1.0)
    if not os.path.exists(wav):
        wav2 = os.path.join(TMP, "fmttest-1.wav")
        wav = wav2 if os.path.exists(wav2) else None
    if not wav:
        print(f"{cand}: 未生成文件"); continue
    r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=codec_name,sample_rate,channels,bits_per_raw_sample",
                        "-of", "default=nw=1", wav], capture_output=True, text=True)
    info = r.stdout.strip()
    print(f"{cand} -> {info}")
    if "pcm_s24le" in info and "48000" in info:
        ok = cand
        break

print("\n选中格式:", ok)
