# CONTINUE.md — pipeline 脚本组 · 历史会话存档（技术要点）

> 性质：早期「全自动管线」阶段的会话交接记录存档（截至 2026-08-21）。现行工作流以 01~09 号文档与 `skill快照/` 为准，本文件只保留仍有复用价值的技术事实。
> 最后更新：2026-08-21（2026-09-21 去个人化整理，技术内容未改判定）

---

## 1. 早期管线在做什么

用 AI 全自动完成「影视/短视频画面 → 音效贴片」：
**视频画面理解（Qwen-VL 事件识别）→ 检索本地音效库（资产表）→ Reaper 自动分轨布置**。
最终目标：给一段视频，Reaper 里自动长出"分好轨、挂好 FX、粗混可用"的音效草稿。

> 后续实际走向：视觉全自动路线被「人工复核的逐秒动作分析报告」取代（见 `skill快照/video-action-analysis/`）；检索引擎（search_assets.py + 资产表 DB）持续服役并成为现行工作流核心（见 04 号文档）。本目录其余脚本作历史参考。

## 2. 阶段成果（存档时已完成 ✅）

| 环节 | 状态 | 说明 |
|---|---|---|
| 音效库资产表 | ✅ | 5.5 万级 WAV → SQLite 资产表（FTS5，分钟级建完） |
| 检索 | ✅ | FTS5 全文 + LLM 同义词扩展，毫秒级查表 |
| 视觉识别 | ✅ | Qwen-VL（qwen-vl-plus）逐帧识别事件 → cue 单 |
| Reaper 直连 | ✅ | reapy_boost 0.10.201 连 Reaper 7.52，插音频/视频/设音量 |
| 全链路演示 | ✅ | 测试视频识别 78 条 cue → 检索 78/78 全部命中布置进 Reaper |
| 视频轨导入 | ✅ | 测试视频（94.72s）已导入 Reaper，画面/波形正常 |

## 3. 目录结构（`pipeline/`）

```
config.json           # 音效库 roots / 端口 / 检索权重（唯一要改的配置）
build_asset_db.py     # 资产表构建：提取 bext 描述/UCS类别/cue区域 → SQLite
search_assets.py      # 检索：LLM 同义词扩展 + FTS5 全文 + 中文类别 LIKE（现行服役）
vision.py             # 画面理解：ffmpeg 抽帧 + Qwen-VL 事件检测 → cue_sheet.json
reaper_stage.py       # Reaper 操作：connect / place_clip（插媒体、cue偏移、音量）
pipeline.py           # 整链编排：视觉→检索→Reaper 布置
setup_reaper.py       # Reaper 侧一键配置（reapy_boost 启用，含 Python 3.13 补丁）
setup_project.py      # 启动 Reaper 后建视频轨导入视频
asset_library.db      # ★ 当前检索用的资产表（本机版；NAS 版为 asset_library_nas.db）
library_index.json    # 旧 JSON 索引（已被 SQLite 取代，备用）
retriever.py          # 已弃用（向量/旧检索），勿用
```

## 4. 关键决策（原项目制作人拍板）

1. **弃用向量化**：全量 embedding 被喊停（效率低），改用「资产表 + 标签 + 同义词扩展」，建表分钟级 + 检索毫秒级。
2. **资产表方案**：利用 Boom Library 自带的 bext 描述（43% 文件有，质量高）+ 目录中文类别 + 英文文件名。
3. **视觉输出英文标签**：Qwen-VL prompt 改为输出英文检索词（如 "footstep concrete"）。
4. **sea→wave 语义检索**：靠 LLM 一次调用扩同义词（sea→ocean,waves,shore...）再查表，复刻 Nuendo Media Bay 效果。
5. **分轨模板方向**（存档时讨论中，后由「模板定稿、每集只填数据表」路线落地，见 09 号文档）：轨道聚合数、中英文轨名、模板来源（Nuendo 导入 vs 脚本生成）。

## 5. 环境配置（换机/重装参考，路径均为历史实例写法）

- Reaper 7.52：`C:\Program Files\REAPER (x64)\reaper.exe`（目录名带空格括号）
- Reaper 资源目录：`C:\Users\<用户>\AppData\Roaming\REAPER\`
- Python：任一装有 reapy_boost 的 Python 3.13（Reaper 内嵌 Python 同用一套）
- DashScope Key：环境变量 `DASHSCOPE_API_KEY`（qwen-vl-plus 视觉 + qwen-turbo/plus 同义词扩展）
- 音效库：`D:\音效文件\`（roots 见 config.json；NAS 机器见 00 号「音源库双版本」）
- VLC 3.0.23 已装（Reaper 视频解码用）：`C:\Program Files\VideoLAN\VLC`

## 5.5 模板（Nuendo 迁移成果）

- **最终模板文件**：`Desktop\Reaper音效模板\音效工作流模板.rpp`（346KB，60 轨 / 4 rv 效果轨 / 12 发送 / 部分 FX 链）
- 迁移链路：Nuendo 14/15 导出 DAWproject → ProjectConverter 1.2.14（GUI，人工转，选 Arrangement）→ Reaper 打开
- **ProjectConverter 局限**：role=effect 的 Channel（混响轨）会丢、轨道路由/发送不转（rpp 里 AUXRECV=0）——需要重建脚本处理
- 重建脚本（`rebuild_routing.py` / `merge_template.py`）留在原机未收入本包：按 dawproject 解析的发送图重建 4 条 rv 效果轨 + 12 条 pre-fader 发送
- Nuendo 原始路由：干声/动作/环境轨 pre 发送到 4 个混响（室内rv/室外rv/心声rv/走廊rv）
- ⚠️ 存档时待办：走廊rv 轨还没挂混响插件（其他 3 条 rv 转换时带了 FX）；总线/编组接收（对话→对话bus 等）也未重建（ProjectConverter 生成的 bus 轨是空壳）
- rpp 保存陷阱：`Main_SaveProjectEx` 只存一轨（bug）；正确做法 `Main_SaveProject(proj,0)` 保存到工程关联路径后复制；发送在 rpp 里是 `AUXRECV 数字...` 空格格式（非 `<AUXRECV>` 块）

## 6. 踩过的坑（避免重踩）

1. **reapy_boost 的 connect 是"类"**：`reapy_boost.connect(Host(IPv4Address('127.0.0.1')))`，不是函数。`connect_to_default_machine()` 有漏传参 bug。
2. **reapy_boost reascript_api 部分函数传参 bug**：GetMediaSourceLength / GetMediaSourceType / PCM_Source_BuildPeaks / InsertMedia / KB_EnumActions 会报 missing p1 或不存在。**绕开**：用 reapy_boost 对象方法（Source.length()、src.type、src.filename）。
3. **Python 3.13 + reapy_boost 配置 bug**：CaseInsensitiveDict 与 configparser 不兼容 → `setup_reaper.py` 里打了 monkey-patch。
4. **API 创建的 item 不自动建峰值**：波形显示需人工执行 Reaper 的 action「Peaks: Build any missing peaks」（Item 菜单）。以后导入视频尽量让人工直接拖入。
5. **指针有效性判断**：正则取 `0x` 后十六进制判非零，别用 `"0x0" in str(id)`（合法指针也含 0x0）。
6. **DashScope embedding batch 上限 10 条**（超了 400 报错）。
7. **视频画面**：Reaper 的视频 item 轨道上只显示波形不显示帧；画面在 View → Video window 看（Ctrl+Shift+V）。
8. **⚠️ 轨道推子 D_VOL 是「线性值」不是 dB**（2026-08-21 事故教训）：`SetMediaTrackInfo_Value(track,"D_VOL",v)` 的 v 单位是线性（0=静音，1=0dB，2=+6dB）。**别做 lin2db 转换**——设成负数会把推子打成 -inf（表现为"推子到底"）。Nuendo dawproject 的 Volume 值（linear）可直接原样传入。
9. **Reaper bus 轨（ISBUS=1）推子显示 -inf 是正常的**（bus 轨不靠推子调音量）——folder 轨若是 bus 态推子 -inf 不是故障；要恢复推子需把 ISBUS 改 0（但 ProjectConverter 生成的 folder 轨 ISBUS=1 是 folder 正常标记，是否要改取决于需求）。

## 7. 存档时的下一步规划（仅作历史记录）

> 以下为存档当时的待办清单，实际走向以 12 号变更记录与现行文档为准。

1. 分轨模板 + 冲突检测分配（后由 09 号「模板定稿、每集只填数据表」路线承接）
2. 布置手感：intensity→音量映射、位置/增益随机微调、同音效变体轮换（后由 20260916 音量铁律收敛为 D_VOL 恒 1.0）
3. 视觉重跑对比 cue 质量（后由人工复核报告路线取代）
4. 一键工作流固化（后由 skill 化工作流承接）
5. REAPER MCP 封装（未实施）

## 8. 常用命令

```bash
cd scripts/pipeline   # 用装有 reapy_boost 的 Python 执行

# 重建资产表（库有新增时）
python -u build_asset_db.py

# 测试检索
python -u search_assets.py "sea" "footstep concrete" "摔倒"

# 全链路：视频 → 视觉识别 → 检索 → Reaper 布置（历史演示路线）
python -u pipeline.py "<视频绝对路径>" 1.0
```

## 9. 模板迁移当时的进展（存档）

**背景**：当时发现删 bus 轨会丢 bus 上的效果器（对话 bus 3 插件等）。用 ProjectConverter **重新转换** dawproject → 完整版 rpp（59 轨、bus 带 FX、12 条发送、推子线性正确）。

**merge_template.py（当时核心工具，未收入本包）**：把 bus 轨的 FX + VOLPAN + ISBUS 合并进 folder 轨，删 bus 轨，删冗余（输入/输出、干声）。
- 当时状态：已生成 `Desktop\Reaper音效模板\音效工作流模板.rpp`（52 轨）
- ✅ 已验证：52 轨加载正常、folder 推子全对（对话0.289/环境fx0.577/动作fx0.616/过渡fx0.414/BGM0.202/总输出0.719）、bus 全删、发送 12 条
- ⏳ 存档时待验证：folder 轨的 FX 加载（CLA-2A/Pro-Q 3/SSLComp/L2 等）——最后一次缩进修复（FXCHAIN 加 4 空格 + 去空行）刚跑完未验证。若 folder FX 仍 =0，检查 FXCHAIN 插入格式（对比总输出轨的 FXCHAIN 缩进）
- ⏳ 存档时待办：走廊 rv（Altiverb 7）扫描问题（插件红）；注册 Reaper 模板库（ProjectTemplates）；环境fx/动作fx bus 无 FX（空壳，正常）

**技术要点（已踩坑）**：
- Reaper 轨道推子 `D_VOL` 是**线性值**（1=0dB），设负数→推子 -inf（详见第 6 节第 8 条）
- `ISBUS 1 1` = folder/bus 态（推子 -inf 正常）；`ISBUS 0 0` = 普通轨有推子
- rpp 文本编辑：`<TRACK` 前有空格（split 用 `\n\s*<TRACK`）；FXCHAIN 块结束是 `>`（不是 `</FXCHAIN>`）；FXCHAIN 插入必须 4 空格缩进、紧贴 TRACK 头 `>` 后、无空行
- 发送（AUXRECV）格式：无尖括号行 `AUXRECV <src_idx> ...`（写在接收轨块内）
- 完整版的 12 条发送全部指向 rv 混响轨（室内rv/室外rv/心声rv/走廊），与 bus 无关
