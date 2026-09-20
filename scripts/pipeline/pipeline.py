"""编排：视觉 cue 单 -> 资产表检索 -> Reaper 布置。

阶段 2 画面理解由 vision.py 实现（ffmpeg 抽帧 + Qwen-VL 事件检测，输出英文标签）。
检索走资产表（index/asset_library.db，FTS5 全文 + 同义词扩展），不扫库不向量化。
完整链路：python pipeline.py <video> [fps]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from reaper_stage import connect, place_clip, ClipSpec
from search_assets import search
from vision import vision_to_cues

BASE_DIR = Path(__file__).resolve().parent


def run(cue_sheet: list[dict], cfg: dict) -> list[dict]:
    db_path = str(BASE_DIR / "index" / "asset_library.db")
    reaper = connect(cfg["reaper"]["host"], cfg["reaper"]["port"])
    placed: list[dict] = []
    for cue in cue_sheet:
        hits = search(db_path, cue["query"], top_k=cfg["retrieval"]["top_k"])
        if not hits:
            placed.append({"cue": cue, "status": "no_match", "action": "人工补音效"})
            continue
        top = hits[0]
        spec = ClipSpec(
            path=top.path,
            start_sec=cue["ts"],
            cue_offset_sec=top.cue_offset_sec,
            cue_len_sec=top.cue_len_sec,
            track_index=max(0, cfg["reaper"]["media_track"] - 1),
        )
        place_clip(reaper, spec)
        placed.append({"cue": cue, "status": "placed", "clip": top.path, "score": top.score})
    return placed


if __name__ == "__main__":
    cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
    if len(sys.argv) >= 2:
        video = sys.argv[1]
        fps = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        print(f"画面理解中: {video} @ {fps} 帧/秒 ...")
        cues = vision_to_cues(video, fps=fps)
        Path("cue_sheet.json").write_text(
            json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"cue 单 {len(cues)} 条 -> cue_sheet.json")
    else:
        # 无视频参数：用演示 cue 单
        cues = [
            {"ts": 3.2, "type": "footstep", "query": "脚步 石板 中速"},
            {"ts": 8.7, "type": "door_creak", "query": "门 吱呀 木头"},
        ]
    result = run(cues, cfg)
    print(json.dumps(result, ensure_ascii=False, indent=2))
