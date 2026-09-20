"""混合检索 (阶段 4 + 5 的检索部分)。

关键词（UCS 名 / 类别 / cue 标签）+ 向量（可选，需 embeddings 已构建）。
向量默认关闭（config.embedder.mode = "none"），先让关键词检索可跑通；
后续接 sentence-transformers 或 Ollama 再开向量加权。
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Candidate:
    path: str
    name: str
    score: float
    cue_offset_sec: float = 0.0
    cue_len_sec: float | None = None
    category: str = ""


def _tok(s: str):
    return [t for t in re.split(r"[\s_\-./]+", s.lower()) if t]


def load_index(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def keyword_score(query: str, rec: dict) -> float:
    """子串匹配评分（中文友好：无需分词，查询词是文本子串即命中）。"""
    q = [t for t in re.split(r"[\s,，、;；]+", query) if t]
    if not q:
        return 0.0
    hay = " ".join(
        [
            rec.get("name", ""),
            rec.get("category", ""),
            rec.get("subcat", ""),
            " ".join(c.get("label", "") for c in rec.get("cues", [])),
        ]
    ).lower()
    hits = sum(1 for t in q if t.lower() in hay)
    return hits / len(q)


def load_embeddings(path: str) -> dict:
    """加载 embeddings.npz -> {path: vec}。"""
    d = np.load(path, allow_pickle=True)
    return dict(zip(d["paths"].tolist(), d["vecs"]))


def _norm_cos(a, b) -> float:
    """余弦相似度映射到 0..1（检索打分用）。"""
    dot = float(np.dot(a, b))
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    return (dot / (na * nb) + 1.0) / 2.0 if na and nb else 0.0


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(
    index: dict,
    query: str,
    top_k: int = 8,
    kw_weight: float = 0.5,
    vec_weight: float = 0.5,
    embeddings: dict | None = None,
    embed_query=None,
) -> list[Candidate]:
    cands: list[Candidate] = []
    qv = embed_query(query) if (embeddings is not None and embed_query is not None) else None
    for rec in index.get("clips", []):
        ks = keyword_score(query, rec)
        vs = 0.0
        if qv is not None:
            ev = embeddings.get(rec["path"])
            if ev is not None:
                vs = _norm_cos(qv, ev)
        score = kw_weight * ks + vec_weight * vs
        if score <= 0:
            continue
        cue = rec["cues"][0] if rec.get("cues") else None
        cands.append(
            Candidate(
                rec["path"],
                rec["name"],
                score,
                cue.get("offset_sec", 0.0) if cue else 0.0,
                cue.get("len_sec") if cue else None,
                rec.get("category", ""),
            )
        )
    cands.sort(key=lambda c: c.score, reverse=True)
    return cands[:top_k]
