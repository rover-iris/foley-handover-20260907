# 本目录使用说明（2026-09-16 整理）

## 首选模板

| 文件 | 用途 |
|---|---|
| **place_ep_template.py** | **当前引擎定稿**（与 skill快照/reaper-foley-workflow/scripts/ 一致）：强制 D_VOL=1.0、D_STARTOFFS 显式写、幂等防重、三重自检。新工程一律抄它，只填 BASE + CUES 数据区 |
| create_video_regions.py | 逐集 Region 幂等创建（视频 API 直贴后的补救；对账只比位置，包装层坑已内置规避） |
| audit_offsets.py | 全工程 off+len 越界审计（对 DB duration 全量比对，可续跑） |
| export_stems_v4.py | 分轨导出定稿版（逐轨 solo + 41824 同步渲染，见 06 号文档） |
| render_format_test.py | 渲染格式探针：2 秒试条 + ffprobe 验证 |

## 历史示例（仅供对照参考，别当模板抄）

| 文件 | 状态 |
|---|---|
| place_ep26_v1.py / place_ep27_29_30_v1.py / place_ep28_v1.py / place_权臣CP01_v1_20260910.py | 老项目真实用过的脚本。**vol 赋值行已于 20260916 中和为强制 1.0**（旧版 vol 列真值生效，曾致 531 条被调量返工）；其余逻辑（连接/防重/贴轨）仍可参考，但自检轨区间是老工程轨序，照抄前必须换成本工程轨序 |
| insert_video_权臣CP01_20260910.py | 老的单条视频插入脚本。**现役路线**：视频+Region 走 `skill快照/reaper-foley-workflow/scripts/make_video_driver.py`（Lua 驱动定稿）；API 直贴后的 Region 补建用本目录 create_video_regions.py |
| fader_backup_20260831.json | 50 轨推子状态备份样本（改推子前先存 JSON 的格式参考） |

## 铁律提醒（20260916 版，详见 04/05 号文档）

1. 音量一律默认 1.0，任何 vol 经验值（0.5~0.8 / 0.3~0.5）均为废止值。
2. start_offset 默认 0；非零取窗必须先出 ffmpeg volumedetect 证据（窗口 max > −30dB）。
3. >10s 杂集类素材默认不作候选。
4. 脚步声归【手动】人工，AI 不选材不贴轨。
5. BASE/偏移只准引用落盘基准表文件，禁止手抄。
