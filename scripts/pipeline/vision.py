"""阶段② 画面理解：视觉模型事件检测 → cue 单。

流程：ffmpeg 抽帧 → Qwen-VL（DashScope compatible-mode）逐帧识别事件
      → 合成 cue 单 [{ts, type, query}]，写入 cue_sheet.json。

用法：
    python vision.py <video> [fps]
    例：python vision.py D:/素材/test.mp4 1.0
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

MODEL = os.environ.get("VL_MODEL", "qwen-vl-plus")
FPS_DEFAULT = 1.0

PROMPT = """你是影视声音设计师的助手，负责从画面帧中识别需要配音效的事件。
分析这张画面，只输出 JSON（不要任何其他文字）：
{"events":[{"type":"音效类型(英文)","query":"英文音效检索关键词(2-4个词，供音效库检索，如 footstep concrete)","intensity":0到1}]}
事件类型示例：footstep / bodyfall / door / weapon / glass / metal / impact / creature / magic / ui / ambience。
若画面无明显事件，输出 {"events":[]}。"""


def _api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        raise RuntimeError("请先设置环境变量 DASHSCOPE_API_KEY")
    return key


def extract_frames(video: str, fps: float = FPS_DEFAULT, out_dir: str = "frames"):
    """抽帧。返回 (帧文件列表, fps)。"""
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    for f in out.glob("*.jpg"):
        f.unlink()
    subprocess.run(
        ["ffmpeg", "-y", "-i", video, "-vf", f"fps={fps},scale=-2:720", "-q:v", "3", str(out / "f_%05d.jpg")],
        check=True,
        capture_output=True,
    )
    frames = sorted(out.glob("*.jpg"))
    return frames, fps


def analyze_frame(frame_path: str) -> dict:
    """Qwen-VL 识别单帧事件，返回 {"events":[...]}。"""
    img_b64 = base64.b64encode(Path(frame_path).read_bytes()).decode()
    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read().decode())
    content = resp["choices"][0]["message"]["content"]
    start, end = content.find("{"), content.rfind("}") + 1
    return json.loads(content[start:end])


def vision_to_cues(video: str, fps: float = FPS_DEFAULT, out_dir: str = "frames", progress=print) -> list[dict]:
    """整链：抽帧 → 逐帧识别 → cue 单。"""
    frames, fps = extract_frames(video, fps, out_dir)
    cues: list[dict] = []
    for i, f in enumerate(frames):
        ts = i / fps
        try:
            result = analyze_frame(str(f))
        except Exception as e:  # noqa: BLE001
            progress(f"帧 {i + 1}/{len(frames)} @ {ts:.1f}s 分析失败: {e}")
            continue
        for ev in result.get("events", []):
            cues.append(
                {"ts": round(ts, 2), "type": ev.get("type", ""), "query": ev.get("query", "")}
            )
        progress(f"帧 {i + 1}/{len(frames)} @ {ts:.1f}s: {len(result.get('events', []))} 个事件")
    cues.sort(key=lambda c: c["ts"])
    return cues


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python vision.py <video> [fps]")
        sys.exit(1)
    video = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else FPS_DEFAULT
    cues = vision_to_cues(video, fps)
    Path("cue_sheet.json").write_text(
        json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"cue 单已写入 cue_sheet.json（{len(cues)} 条）")
