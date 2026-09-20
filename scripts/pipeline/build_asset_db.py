"""资产表构建：全量提取音效库元数据 → SQLite + FTS5 全文索引。

每个文件提取：路径 / 文件名 / 中文目录类别 / bext 描述(官方英文) / cue 区域 / 时长 / 采样率。
输出：index/asset_library.db（assets 表 + cues 表 + assets_fts 全文表）。
之后检索只查这张表，不再扫库。

用法：python build_asset_db.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import struct
import sys
import time
import wave
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from lib_indexer import read_wav_cues  # noqa: E402


def read_bext_desc(path: str) -> str:
    """读 WAV bext chunk 的 Description 字段（前 256 字节，null 截断）。"""
    try:
        f = open(path, "rb")
    except OSError:
        return ""
    with f:
        if f.read(4) != b"RIFF":
            return ""
        f.seek(8, 1)
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            cid = head[:4]
            size = struct.unpack("<I", head[4:8])[0]
            if cid == b"bext":
                body = f.read(min(size, 256))
                return body[:256].split(b"\x00")[0].decode("utf-8", "replace").strip()
            f.seek(size + (size % 2), 1)
    return ""


def read_duration_sr(path: str) -> tuple[float, int]:
    """读 WAV 时长与采样率（wave 模块，失败回退 ffprobe 默认）。"""
    try:
        with wave.open(path, "rb") as w:
            sr = w.getframerate()
            return w.getnframes() / sr if sr else 0.0, sr
    except Exception:
        return 0.0, 0


def read_rating(path: str) -> int:
    """读 Steinberg BWFXML 里的 MediaRating（Cubase/Nuendo 评分，1-5）。

    只读文件尾部 64KB 找 <BWFXML>（位于 data 块之后），正则取 <VALUE>。
    无评分返回 0。
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, size - 65536))
            tail = f.read()
    except OSError:
        return 0
    i = tail.find(b"<BWFXML")
    if i < 0:
        return 0
    m = re.search(rb"<NAME>MediaRating</NAME>\s*<TYPE>int</TYPE>\s*<VALUE>(\d+)</VALUE>", tail[i:])
    if not m:
        return 0
    try:
        return int(m.group(1))
    except ValueError:
        return 0


def resolve_theme(path: str, theme_roots: dict) -> str:
    """按路径前缀匹配主题标记；未命中返回 '通用'。路径统一正斜杠比较。"""
    pl = path.replace("\\", "/").lower()
    for theme, roots in theme_roots.items():
        for r in roots:
            if pl.startswith(r.replace("\\", "/").lower()):
                return theme
    return "通用"


AUDIO_EXTS = (".wav", ".flac", ".aif", ".aiff")


def resolve_official(path: str, root: str) -> str:
    """提取官方包名（official）。规则与 search 侧约定一致，小写存储：
    - Boom：中文分类后的官方子目录名；平铺分类（第二段即文件）→ 中文分类名兜底
    - 中国风 / Sound Morph：一律取库名（root 目录名，剥掉「(爆炸坍塌)」等前缀括号）；
      编号分类（Blasts / Designed Audio 等）在 category 字段体现，不算官方名
    """
    pl = path.replace("\\", "/").lower()
    rn = root.replace("\\", "/").lower().rstrip("/")
    if pl.startswith("d:/音效文件/boom library"):
        segs = pl.split("/boom library/", 1)[1].split("/")
        if len(segs) >= 2:
            if segs[1].lower().endswith(AUDIO_EXTS):
                return segs[0]
            return segs[1]
        return segs[0] if segs else ""
    base = rn.split("/")[-1]
    base = re.sub(r"^[（(][^）)]*[）)]", "", base).strip()
    return base


def main():
    cfg = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
    db_path = BASE_DIR / "index" / "asset_library.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS assets(
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE NOT NULL,
            filename TEXT,
            category TEXT,
            name TEXT,
            desc TEXT,
            duration REAL,
            samplerate INTEGER,
            n_cues INTEGER DEFAULT 0,
            theme TEXT DEFAULT '通用',
            rating INTEGER DEFAULT 0,
            official TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS cues(
            id INTEGER PRIMARY KEY,
            asset_id INTEGER REFERENCES assets(id),
            offset_sec REAL,
            len_sec REAL,
            label TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts5(
            name, desc, category, content='assets', content_rowid='id'
        );
        CREATE TRIGGER IF NOT EXISTS assets_ai AFTER INSERT ON assets BEGIN
            INSERT INTO assets_fts(rowid, name, desc, category)
            VALUES (new.id, new.name, new.desc, new.category);
        END;
        """
    )
    conn.commit()

    roots = list(cfg["library"]["roots"])
    theme_roots = cfg["library"].get("theme_roots", {})
    # theme_roots 里的路径同样作为扫描根（去重）
    for r in theme_roots.values():
        for p in r:
            if p not in roots:
                roots.append(p)
    wav_exts = {".wav", ".flac", ".aif", ".aiff"}
    total = 0
    t0 = time.time()
    for root in roots:
        root_p = Path(root)
        for idx, p in enumerate(root_p.rglob("*")):
            if p.suffix.lower() not in wav_exts:
                continue
            # 增量模式：已入库的路径跳过（防止重跑撞 UNIQUE 中断）
            if conn.execute("SELECT 1 FROM assets WHERE path=?", (str(p),)).fetchone():
                continue
            rel = p.relative_to(root_p)
            category = rel.parts[0] if len(rel.parts) > 1 else ""
            desc = read_bext_desc(str(p))
            cues = read_wav_cues(str(p))
            dur, sr = read_duration_sr(str(p))
            theme = resolve_theme(str(p), theme_roots)
            rating = read_rating(str(p))
            official = resolve_official(str(p), root)
            conn.execute(
                "INSERT INTO assets(path, filename, category, name, desc, duration, samplerate, n_cues, theme, rating, official)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (str(p), p.name, category, p.stem, desc, dur, sr, len(cues), theme, rating, official),
            )
            asset_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.executemany(
                "INSERT INTO cues(asset_id, offset_sec, len_sec, label) VALUES(?,?,?,?)",
                [(asset_id, c.get("offset_sec", 0.0), c.get("len_sec"), c.get("label", "")) for c in cues],
            )
            total += 1
            if idx % 5000 == 0 and idx:
                el = time.time() - t0
                print(f"  ...{idx} 个 ({el:.0f}s)")
            conn.commit()  # 每文件提交一次，防止中断丢进度

    conn.commit()
    # official 存量回填：历史行 / 备份恢复的库里 official 可能为空（该列晚于建库脚本加入）
    empty = conn.execute(
        "SELECT id, path FROM assets WHERE official IS NULL OR official=''"
    ).fetchall()
    if empty:
        for aid, p in empty:
            off = ""
            for r in roots:
                if p.replace("\\", "/").lower().startswith(r.replace("\\", "/").lower().rstrip("/")):
                    off = resolve_official(p, r)
                    break
            conn.execute("UPDATE assets SET official=? WHERE id=?", (off, aid))
        conn.commit()
        print(f"official 回填: {len(empty)} 条")

    print(f"完成: {total} 条 -> {db_path} ({db_path.stat().st_size/1e6:.1f} MB, 用时 {(time.time()-t0)/60:.1f} 分钟)")
    conn.close()


if __name__ == "__main__":
    main()
