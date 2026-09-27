"""本地音效库索引构建 (数据底座 / 阶段 4 的前置)。

遍历 roots 下的 WAV，解析 UCS 命名 + WAV Cue 区域，产出 index/library_index.json。
NAS 路径：仅读取，绝不写入原文件。
单文件多音效靠 WAV Cue 点 + labl 标签解（offset_sec 定位到具体音效段）。
"""
from __future__ import annotations

import json
import re
import struct
import wave
from pathlib import Path

WAV_EXTS = {".wav", ".flac", ".aif", ".aiff"}


def parse_ucs(name: str) -> dict:
    """轻量 UCS 解析。

    Cat [Subcat] - Name.Variant  或  Cat_Subcat_Name_Variant
    只取 category / subcat / name 三段，够检索用。
    """
    stem = Path(name).stem
    category = subcat = ""
    if "[" in stem and "]" in stem:
        pre, _, rest = stem.partition("[")
        subcat, _, after = rest.partition("]")
        category = pre.strip().rstrip("-_ ").strip()
        name_part = after.strip().lstrip("-_ ").strip() or pre
    else:
        parts = re.split(r"[_\-]", stem)
        if len(parts) >= 3:
            category, subcat, name_part = parts[0], parts[1], parts[-1]
        elif len(parts) == 2:
            category, name_part = parts[0], parts[1]
        else:
            name_part = stem
    return {"category": category, "subcat": subcat, "name": name_part}


def read_wav_cues(path: str) -> list[dict]:
    """解析 WAV cue 点 + labl 标签 -> [{offset_sec, label}]。

    单文件多音效靠此解：每个 cue 点是一个独立音效的起点。
    只读取文件头部与 cue/LIST chunk，跳过 data（避免大文件全读进内存）。
    """
    cues: dict[int, int] = {}
    labels: dict[int, str] = {}
    try:
        f = open(path, "rb")
    except OSError:
        return []
    with f:
        if f.read(12)[:4] != b"RIFF":
            return []
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            cid = head[:4]
            size = struct.unpack("<I", head[4:8])[0]
            if cid == b"cue ":
                body = f.read(size)
                cnt = struct.unpack("<I", body[:4])[0]
                p = 4
                for _ in range(cnt):
                    if p + 24 > len(body):
                        break
                    dw_name = struct.unpack("<I", body[p : p + 4])[0]
                    sample_off = struct.unpack("<I", body[p + 12 : p + 16])[0]
                    cues[dw_name] = sample_off
                    p += 24
            elif cid == b"LIST":
                body = f.read(size)
                if body[:4] == b"adtl":
                    j = 4
                    while j + 8 <= len(body):
                        sub = body[j : j + 4]
                        ssz = struct.unpack("<I", body[j + 4 : j + 8])[0]
                        sbody = body[j + 8 : j + 8 + ssz]
                        if sub == b"labl":
                            dw_name = struct.unpack("<I", sbody[:4])[0]
                            txt = sbody[4:].split(b"\x00")[0].decode("utf-8", "ignore")
                            labels[dw_name] = txt
                        j += 8 + ssz
            else:
                f.seek(size, 1)
            if size % 2:
                f.seek(1, 1)

    sr = _samplerate(path)
    out = []
    for name, off in cues.items():
        out.append({"offset_sec": off / sr if sr else 0.0, "label": labels.get(name, "")})
    return out


def _samplerate(path: str) -> int:
    try:
        with wave.open(path, "rb") as w:
            return w.getframerate()
    except Exception:
        return 44100


def build_index(roots: list[str], out_path: str) -> int:
    clips = []
    for root in roots:
        root_p = Path(root)
        for idx, p in enumerate(root_p.rglob("*")):
            if p.suffix.lower() not in WAV_EXTS:
                continue
            # 目录级分类：Boom Library 等库把类别放在第一级目录名里
            rel = p.relative_to(root_p)
            dir_cat = rel.parts[0] if len(rel.parts) > 1 else ""
            meta = parse_ucs(p.name)
            cues = read_wav_cues(str(p))
            clips.append(
                {
                    "path": str(p),
                    "name": meta["name"] or p.stem,
                    "category": dir_cat or meta["category"],
                    "subcat": meta["subcat"],
                    "cues": cues,
                    "n_cues": len(cues),
                }
            )
            if idx % 5000 == 0 and idx:
                print(f"  ...已处理 {idx} 个文件")
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        json.dumps({"clips": clips}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return len(clips)


if __name__ == "__main__":
    import json as _json

    cfg = _json.loads(Path("config.json").read_text(encoding="utf-8"))
    n = build_index(cfg["library"]["roots"], cfg["index"]["out"])
    print(f"索引完成：{n} 个音效文件 -> {cfg['index']['out']}")
