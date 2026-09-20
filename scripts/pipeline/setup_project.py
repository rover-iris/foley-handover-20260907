"""新建工程并导入视频轨（Reaper 已由外部启动后运行）。

用法：python setup_project.py <video_path>
"""
from __future__ import annotations

import sys
import time

import reapy_boost

from reaper_stage import connect


def wait_ready(retries: int = 12, delay: int = 3):
    """等 Reaper 的 Distant API 就绪（启动后 web interface 需要几秒）。"""
    for i in range(retries):
        try:
            reapy = connect()
            proj = reapy.Project()
            _ = proj.name  # 触发一次真实 RPC，验证链路
            return reapy
        except Exception as e:  # noqa: BLE001
            print(f"  等待 Reaper 就绪 {i + 1}/{retries} ... ({type(e).__name__})")
            time.sleep(delay)
    raise RuntimeError("Reaper 一直未就绪，请确认已启动")


def main():
    video = sys.argv[1] if len(sys.argv) > 1 else r"D:\视频\测试片\02.mp4"
    reapy = wait_ready()
    proj = reapy.Project()
    RPR = reapy.reascript_api

    # 清空（若已有残留）
    for it in list(proj.items):
        it.delete()
    for tr in list(proj.tracks):
        tr.delete()

    track = proj.add_track()
    track.name = "视频"
    src_id = RPR.PCM_Source_CreateFromFile(video)
    src = reapy_boost.Source(src_id)
    item = track.add_item(start=0.0, length=src.length())
    take_id = RPR.AddTakeToMediaItem(item.id)
    take = reapy_boost.Take(take_id)
    take.source = src
    print(f"完成: 视频轨 {track.name!r} | item@{item.position:.2f}s 长{item.length:.2f}s")
    print(f"工程: {proj.n_tracks} 轨 / {proj.n_items} item")
    print("请用 View → Video window 或双击视频 item 查看画面")


if __name__ == "__main__":
    main()
