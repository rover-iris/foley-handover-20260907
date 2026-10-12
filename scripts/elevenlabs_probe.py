# -*- coding: utf-8 -*-
"""ElevenLabs 连通自测 + 配乐实测探针（13 号文档 Phase 0/2）。

用法：
  set ELEVENLABS_API_KEY=<key>          # key 走环境变量，禁止写进文件/入库
  python elevenlabs_probe.py                     # Phase 0：连通 + 2s 音效 + 不烧大钱
  python elevenlabs_probe.py --music 视频.mp4 --out 目录   # Phase 2 快捷路：整集 video_to_music
  python elevenlabs_probe.py --compose "prompt" --ms 69000 --out 目录  # Phase 2 精确路：compose_music

纪律：每次生成烧 credits（音乐 900/分钟）——prompt 先打磨再发，禁止当抽卡机；
免费档产物禁商用，产物文件名自动带档位标记需人工确认。
"""
import os
import sys
import time


def main():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("[FAIL] 未设 ELEVENLABS_API_KEY 环境变量")
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        sys.exit("[FAIL] 未装 SDK：pip install elevenlabs")
    client = ElevenLabs(api_key=key)

    out_dir = "."
    if "--out" in sys.argv:
        out_dir = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(out_dir, exist_ok=True)

    if "--music" in sys.argv:  # 快捷路：整集 video_to_music
        video = sys.argv[sys.argv.index("--music") + 1]
        desc = "cinematic score, leave room for dialogue"
        if "--desc" in sys.argv:
            desc = sys.argv[sys.argv.index("--desc") + 1]
        print(f"video_to_music: {video}（按视频时长计费 900 credits/分钟，确认后 5s 内 Ctrl+C 取消）")
        time.sleep(5)
        with open(video, "rb") as v:
            audio = client.music.video_to_music(videos=[v], description=desc, model_id="music_v2")
        out = os.path.join(out_dir, "v2m_draft.mp3")
        with open(out, "wb") as f:
            f.write(b"".join(audio))
        print(f"[OK] 落盘 {out}")

    elif "--compose" in sys.argv:  # 精确路：compose_music 指定毫秒
        prompt = sys.argv[sys.argv.index("--compose") + 1]
        ms = int(sys.argv[sys.argv.index("--ms") + 1]) if "--ms" in sys.argv else 69000
        print(f"compose_music: {ms/1000:.1f}s（约 {900*ms/60000:.0f} credits，5s 内 Ctrl+C 取消）")
        time.sleep(5)
        audio = client.music.compose(prompt=prompt, music_length_ms=ms,
                                     model_id="music_v2", force_instrumental=True)
        out = os.path.join(out_dir, f"compose_{ms//1000}s.mp3")
        with open(out, "wb") as f:
            f.write(b"".join(audio))
        print(f"[OK] 落盘 {out}")

    else:  # Phase 0：最小连通（2s 音效 ≈ 30 credits）
        print("Phase 0 连通自测：生成 2s 测试音效（约 30 credits，5s 内 Ctrl+C 取消）")
        time.sleep(5)
        audio = client.text_to_sound_effects.convert(
            text="soft wind chime, single gentle ring", duration_seconds=2.0)
        out = os.path.join(out_dir, "phase0_test.mp3")
        with open(out, "wb") as f:
            f.write(b"".join(audio))
        print(f"[OK] 落盘 {out}——能播放即链路通")


if __name__ == "__main__":
    main()
