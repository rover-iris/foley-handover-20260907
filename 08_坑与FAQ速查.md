# 08 · 坑与 FAQ 速查

> 出问题先查这张表。每一条都是实机上踩出来的，不是理论。

## REAPER API / reapy

| 现象 | 原因 | 解法 |
|------|------|------|
| reapy 脚本 exit 1、零输出、无报错 | reapy 偶发段错误 | 直接重跑。脚本要幂等（防重机制保证不贴重）。要诊断时用 `runpy` + `faulthandler` 包一层重跑 |
| connect 后第一个调用失败 | 连接未稳定 | connect 后 `time.sleep(1)` |
| start_offset 传了但取窗没生效 | 没写 take 属性 | 必须显式 `SetMediaItemTakeInfo_Value(take,'D_STARTOFFS',off)`。引擎级坑，见 05 号文档 |
| `Main_SaveProject(0)` 报缺参 | reapy 缺该函数封装 | 用 `Main_SaveProjectEx(0, 工程路径, 0)` |
| 保存后退出仍弹"是否保存" | PROJECT_ISDIRTY 假阳性（保存后 dirty 标志没清） | 保存后执行 `RPR.GetSetProjectInfo(0,'PROJECT_ISDIRTY',0,True)` 强制清零，再 `Main_OnCommand(40004,0)` 退出，实测无弹窗 |
| `GetTrackUIVolPan` 取返回值 [1] 报错 | 返回是 `(retval, track*, vol, pan)` 四元组 | vol 在 `[2]`，pan 在 `[3]` |
| 循环里渲染秒退、文件 0MB | 用了 42230（异步渲染命令） | 换 41824（同步渲染） |
| 渲染出的分轨内容全静音 | RENDER_SETTINGS=3 (stems) 模式 bug，根因未明 | 放弃 stems，用 solo-loop 方案（06 号文档） |
| 某条分轨整条静音（其余正常） | 渲染期间被人手动暂停过，首遍被污染 | **原样重渲该条即愈**。终验必须逐条 volumedetect |
| 防重跳过导致"新增 0 条" | 计数器只在新增时累加 | 用区间对账（数 item）判断成败，别信计数器 |
| `GetProjectName("",512)` TypeError | 出参缓冲区参数必须传全 | `GetProjectName(proj,"",512)`；`EnumProjects(-1,"",512)` 同理（20260910 实测） |
| `GetTrackName` 取 [1] 拿到指针串 | 返回 (retval, track*, name) | 名字在下标 [2] |
| 条目名「改了没生效」 | P_NAME 读回易取到键名位 | 条目名落盘与否以 .rpp 内 `NAME` 行为准，不以日志打印为准 |
| .rpp 文本统计漏计数 | 文件是 CRLF 换行 | 跨行正则要吃 `
`（曾误判「只存 1 条」） |
| `CountProjectMarkers(0,0,0)` 的 markers/regions 出参恒 0 | reapy_boost 网络通道出参不回传（20260916 实测） | 总数取返回值 [0]；明细逐条 `EnumProjectMarkers` 枚举、按位置比对 |
| `EnumProjectMarkers` 名称出参返回占位串 | 字符串出参回显传入的占位符 | 对账只比位置不比名称；删 marker 按返回值末位 **marker id**（枚举序号≠id，按序号删曾误删一条） |
| `CountProjectMarkers(0,0,0)` 的 markers/regions 出参恒 0 | reapy_boost 网络通道出参不回传（20260916 实测） | 总数取返回值 [0]；明细逐条 `EnumProjectMarkers` 枚举、按位置比对 |
| `EnumProjectMarkers` 名称出参返回占位串 | 字符串出参回显传入的占位符 | 对账只比位置不比名称；删 marker 按返回值末位 **marker id**（枚举序号≠id，按序号删曾误删一条） |

## 连接层 / 环境陷阱（2026-09-09 补录，全部实测）

| 现象 | 原因 | 解法 |
|------|------|------|
| `RPR.CountTracks` 报 AttributeError（module has no attribute） | **reapy_boost 空壳**：import 时自动 connect 失败 → 函数表没注册，且 DisabledDistAPIError 被 connect **静默吞掉**——「connect 不报错」是假象 | ①脚本**顶部**（import reapy_boost 之前）清掉 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY 并设 NO_PROXY=127.0.0.1,localhost；②connect 后**必须调用一次真函数断言**（`hasattr(RPR,'CountTracks')`），失败就退出，别带病跑 |
| curl/python 到 2308/2309 全挂或 502 | 本机代理 `HTTP_PROXY=127.0.0.1:53714` 劫持了对 127.0.0.1 的请求（urllib 也会读它！） | curl 加 `--noproxy "*"`；python 清环境变量（同上） |
| 触发激活动作返回 200 但什么都不执行 | **reaper-kb.ini 损坏**（曾发生：整个文件无换行，多条 SCR 粘连成一条废条目 → 运行时动作列表里没有该动作）。本机已修复，坏文件备份 `reaper-kb.ini.corrupt-20260831.bak` | 触发不执行时先 `type reaper-kb.ini` 查行数/格式，SCR 行格式 `SCR 4 0 <ID> "<描述>" <脚本绝对路径>`，每条一行 |
| Python 3.13 下 reapy RPC 挂起/爆栈 | reapy_boost 0.10.201 的 `http.client.parse_headers` 递归解析爆栈 | 脚本顶部打补丁：`sys.setrecursionlimit(20000)` + 覆写 `http.client.parse_headers`（完整代码见 `stemtest\probe_recon2.py` 模板，或桌面 `REAPER-reapy交接_20260909.md`） |
| 进程在、端口在、HTTP 全部超时空响应 | **REAPER 有模态弹窗**（保存询问、渲染窗口等），主线程被堵，Web Interface 一起挂 | 跑 `probe_windows.py`（Win32 只读枚举窗口，EXIT 2=有弹窗）→ 报告用户人工点击。**原则：检测+报告+请人工点，绝不自动化点弹窗** |
| 分不清 REAPER 开没开 / 连不上 | ~~四重对齐~~（2026-09-14 修订）改用 `scripts/connect_reaper.py`：自动找进程→netstat 枚举监听端口→逐个实连→回读工程确认；REAPER 未运行时 AI 可自行启动（制作人已解禁），`--launch` 全自动 |
| ~~激活脚本/2308 监听~~ | （2026-09-14 修订）激活动作流程已弃用：connect_reaper.py 直接对进程监听端口自适应实连（2309 直连即通亦实测）；只有直连全失败时才回退旧激活流程 |

## 上游逐秒报告验收（2026-09-10 补录，全部实证）

| 坑 | 实证 | 防法 |
|------|------|------|
| 报告用「36-45s」合并行，起手点全丢 | 权臣CP V2 重跑 54/54 集，行数仅达要求 20%~50%，且报告自称「逐秒全扫」 | 收货先跑 `check_report.py`（skill快照/video-action-analysis/scripts/），行数 < ceil(时长) 即 FAIL |
| 报告把动作链改写成静态（cue 放错位置） | 「白羽箭横飞→中肩→抓杆」被写成「58s 箭已躺在地上」，帧 s_059/s_060 就在帧库里 | 【自动】事件必须可指认帧证据；对关键动作抽查对应秒的帧图 |
| 报告时间整体 +1s | `s_%03d.jpg` 从 1 起、秒从 0 起，s_059=t=58s，两版报告都按「s_N=第N秒」用 | 秒↔帧以 extract_frames.py 产出的 manifest.json 为准 |
| 环境底衬计入事件统计凑数 | 蝶类「留环境」被算进「【自动】12 个」 | 门禁校验「统计数 > 表内离散事件行」即 FAIL |

## 渲染格式

| 需求 | 值 |
|------|-----|
| RENDER_FORMAT 48k/24bit wav | base64 串 `ZXZhdxgAAAA=`（已 ffprobe 验证 pcm_s24le/48000/24） |
| 同步渲染命令 | `Main_OnCommand(41824, 0)` |
| 渲染完成判断 | 文件 ≥919MB（全时长理论下限）且连续 2 次读数稳定 |

## 沙箱 / 环境类

| 现象 | 解法 |
|------|------|
| python `os.remove` 被拦（SAFE_DELETE_FAIL_CLOSED） | 脚本内不删文件，改用外部 shell 命令 `rm` |
| DB 报 `no such module: fts5` | 换 Python 版本（官方编译版自带 FTS5） |
| bash 里 `python -c` 内联传 UNC/NAS 路径 | 内联反斜杠转义 + SMB 组合下**静默失败**：os.walk 返回 0 文件、exists 恒 False，但不报任何错（2026-09-20 实测，同命令写进 .py 文件即正常） | 访问 NAS 一律先写临时 .py 脚本文件再执行，禁止 `python -c` 内联传 UNC 路径 |

## 工作流类

| 问题 | 解法 |
|------|------|
| AI 报告里的动作在视频里不存在 | 假动作（报告幻觉）。帧证据核验一票否决，剔掉不贴 |
| 报告时间戳与画面对不上 | 以抽帧实际内容为准修正时间 |
| 同一音效一集里反复出现 | 违反选材规则（同源≤2次+异窗轮换），见 04 号文档 |
| 新集不知道 Region 起点 | 用 `EnumProjectMarkers2` 遍历 region 取 pos，不要估算 |

## 保存与关闭（完整流程）

```python
RPR.Main_SaveProjectEx(0, r"工程完整路径.RPP", 0)   # 保存
RPR.GetSetProjectInfo(0, 'PROJECT_ISDIRTY', 0, True) # 清假阳性 dirty
RPR.Main_OnCommand(40004, 0)                          # File: Quit REAPER，无弹窗
```
