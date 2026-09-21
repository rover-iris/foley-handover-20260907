"""Reaper 自动布置骨架 (阶段 6)。

依赖：本机 Reaper 运行中 + reapy_boost 扩展 + Distant API 已启用（见 setup_reaper.py）。
定位：reapy 直连的最小布置骨架（cue 区域级贴音效的底层操作封装）。

cue 区域级贴音效：用 take.start_offset 跳过文件前段，item.length 裁到 cue 长度，
实现「单文件多音效，只取其中一段」。

reapy_boost 注意点：
- connect 是类，需传 Host(IPv4Address(...))
- 插入媒体：PCM_Source_CreateFromFile + Track.add_item + take.source 赋值
- 音量/声像走 Item.set_info_value("D_VOL"/"D_PAN")
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from ipaddress import IPv4Address

import reapy_boost
from reapy_boost.tools.network.machines import Host

log = logging.getLogger("reaper_stage")


def _source_valid(src_id) -> bool:
    """判断 PCM source 指针是否有效（非空指针）。"""
    if not src_id:
        return False
    m = re.search(r"0x([0-9A-Fa-f]+)", str(src_id))
    return bool(m) and int(m.group(1), 16) != 0


@dataclass
class ClipSpec:
    path: str
    start_sec: float
    cue_offset_sec: float = 0.0
    cue_len_sec: float | None = None
    gain_db: float = 0.0
    pan: float = 0.0
    track_index: int = 0


def connect(host: str = "127.0.0.1", port: int | None = None) -> "reapy_boost":
    """连接本机 Reaper。失败抛清晰错误。"""
    try:
        reapy_boost.connect(Host(IPv4Address(host)))
        log.info("已连接 Reaper: %s", reapy_boost.get_reaper_version())
        return reapy_boost
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "连不上 Reaper：确认 Reaper 已启动、Distant API 已启用"
            "（跑过 setup_reaper.py 并重启 Reaper）"
        ) from exc


def ensure_track(reapy: "reapy_boost", index: int):
    """确保目标轨道存在，不存在则新建。"""
    project = reapy.Project()
    tracks = project.tracks
    while len(tracks) <= index:
        project.add_track()
        tracks = project.tracks
    return tracks[index]


def place_clip(reapy: "reapy_boost", spec: ClipSpec):
    RPR = reapy.reascript_api
    track = ensure_track(reapy, spec.track_index)
    src_id = RPR.PCM_Source_CreateFromFile(spec.path)
    if not _source_valid(src_id):
        raise RuntimeError(f"无法从文件创建 source: {spec.path}")
    source = reapy.Source(src_id)
    # 未指定 cue 长度时取源文件全长，避免 0 长度 item 无效
    src_len = source.length() or 0.0
    length = spec.cue_len_sec if spec.cue_len_sec else src_len
    item = track.add_item(start=spec.start_sec, length=length)
    # add_item 创建的 item 没有 take，需手动加 take 再绑 source
    take_id = RPR.AddTakeToMediaItem(item.id)
    take = reapy.Take(take_id)
    take.source = source
    if spec.cue_offset_sec:
        take.start_offset = spec.cue_offset_sec
    if spec.cue_len_sec:
        item.length = spec.cue_len_sec
    if spec.gain_db:
        item.set_info_value("D_VOL", spec.gain_db)
    if spec.pan:
        item.set_info_value("D_PAN", spec.pan)
    log.info(
        "已布置 %s @ %.3fs (cue %.3f+%.3f, gain %.1fdB, pan %.2f)",
        spec.path,
        spec.start_sec,
        spec.cue_offset_sec,
        spec.cue_len_sec or src_len,
        spec.gain_db,
        spec.pan,
    )
    return item
