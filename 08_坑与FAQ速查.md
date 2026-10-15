# 08 · 坑与 FAQ 速查

> 出问题先查这张表。每一条都是实机上踩出来的，不是理论。
> **主从口径**：REAPER 层坑的**执行权威** = `skill快照/reaper-remote-ops` SKILL §7 坑速查表（`[R-01]`~`[R-31]`，编号稳定可引用）；foley 工作流域的坑（假动作/选材/取窗）的**执行权威** = foley skill `references/pitfalls.md`（`[W-xx]`/`[X-xx]`）。本表是人读版入口，只放指针与分层导航，冲突以 skill 为准。

> **分层维护规则（改本表前必读）**：
> 1. if 坑满足「近 3 批内发生 ≥1 次 且 未转化为脚本门禁/条款」→ 现役坑，留本表（现役内容合计 ≤30 行）；
> 2. if 坑已进脚本门禁或条款 → 移 `08_坑与FAQ速查-archive.md`，本表只留指针，引用代替复制，防双份漂移；
> 3. 已移交坑（REAPER API 层 → remote-ops §7；foley 域 → foley skill pitfalls 两册）不复制回本表；
> 4. if 归档坑复发且仍未固化 → 从归档提回本表。

## 现役坑导航（人读版）

- **REAPER 连接 / API / 渲染 / 保存 / rpp 编辑 / 装机**：一律查 `skill快照/reaper-remote-ops` SKILL §7 坑速查表（`[R-01]`~`[R-31]`）与对应正文节（§1 装机连接、§5 保存关闭、§6 渲染导出）。
- **foley 工作流域**（报告核验/选材/音源/贴轨口径）：现役坑查 foley skill `references/pitfalls.md`；已固化坑查 `references/pitfalls-archive.md`（W-01~W-09、X-01~X-07，逐条注明固化去向）。
- **上游逐秒报告验收**：机器门禁 = `skill快照/video-action-analysis/scripts/check_report.py`（行数 < ceil(时长) 即 FAIL、事件须可指认帧证据、统计数 > 离散事件行即 FAIL）；秒↔帧换算以 extract_frames.py 产出的 manifest.json 为准。
- **渲染格式速查**：48k/24bit wav base64 串 `ZXZhdxgAAAA=`；同步渲染命令 `Main_OnCommand(41824, 0)`；完成判断 = 文件 ≥ 理论下限（≈16.5MB/分钟 × 工程时长）且连续 2 次读数稳定（细节权威在 remote-ops §6）。
- **已固化坑人读存档**：`08_坑与FAQ速查-archive.md`（REAPER API、连接层/环境、报告验收、沙箱环境、工作流、保存关闭各节原表）。
