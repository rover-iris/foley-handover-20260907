# 13 · 配乐线设计（ElevenLabs 接入）

> 状态：单路线定稿，主线实测已跑通。本册是配乐线的**设计权威**；实测结论回写本册并记 12 号。
> **修订记录**：2026-10-13 制作人拍板「配乐线单路线化」——双路线（compose_music 正式 / video_to_music 草稿）改为单路线（video_to_music 唯一主线，compose_music 降格特例线）；并入《ElevenLabs 音乐机制调查》（`Desktop\1012测试\cues\ElevenLabs音乐机制调查_20261013.md`，下称「调查报告」）勘误 9 条；废除「双草稿静音互斥贴两轨」施工法（§8 第 2 条）。详录见 12 号 2026-10-13 节。同日制作人拍板职责边界调整：BGM 轨贴入归音乐总监，配乐线自闭环（§8 第 3 条；库内缺货音效仍只生成不贴轨）。
> 音效侧规矩全部沿用（NAS 只读 / 并发 ≤2 / D_VOL 不动 / 脚步不配），配乐是**独立工种**，不进 `/贴轨`。

## 1. 定位与分工

- 配乐目标：**进成片**，一集（约 1 分钟）1~2 个乐段，3 段罕见——按「乐段」不按「首」。
- **生成模型（单路线，2026-10-13 制作人定调）**：视频与约束词**同进一次生成**（video_to_music），约束词（description/tags）的定位 = **对视频理解的约束项**——约束模型、纠正其对视频理解产生的偏差（制作人口径原话：「视频理解+关键词约束同步进行，提示词是约束它、纠正它对视频理解产生的偏差」）。
- **官方定性（黑盒声明，调查报告 Q1/Q2）**：官方对视频理解**零机制描述**，只承诺两点——配乐与视频「相配」（原文 matching the video）、产出时长对齐视频总长；description/tags 官方用词为可选「影响」项（influence），与视频在内部如何融合未公开。**按黑盒对待**：我方分析为权威（可审、有证据），模型为黑盒（结论不可见，只体现于产物）；产物偏离时按我方口径改约束词重新生成（§5），分歧上报制作人。审美终审权 = 制作人耳朵。

## 2. 风格两级制（先验 ≠ 标准）

| 层级 | 内容 | 性质 |
|---|---|---|
| 项目级风格 | 开工前错峰做：抽 2~3 集代表集（首/中/高潮）粗看定整体风格 → 写进 `foley_project.json` 的 `music_style` 字段（风格名 + tags + 描述句式） | 先验，可推翻 |
| 单集基调 | 默认继承项目风格；只写乐段划分 + 避让对白段 + 偏离检查 | 继承或覆盖 |
| 段级现实 | 画面内容优先于标签（古风剧里穿越者掏枪 = 该段切现代/混搭，不强行古风）——与选材「声源存在性」同哲学：标签是降权不是禁区；偏离段写进 brief 约束词显式纠偏 | 硬约束 |

偏离检测问法：「这段的画面还属于项目风格吗」——分析师动作报告里看得见答案。

## 3. 时长规则

1. 乐段时长**由我方按画面段落算死**（起点~终点，精确到秒）——用于 brief 约束词与贴轨裁切落点；
2. **主线（video_to_music）无时长参数**：产出时长自动对齐输入视频总长（官方口径；实测吻合，见 §10）。一集一次生成，输入整集视频；
3. **特例线（compose_music）毫秒级可控**：请求时长 = 判定时长 **+15% 且至少 +2 秒**（容错余量，宁长勿短）；时长合法区间 3000~600000 ms（官方，越界拒绝）；
4. 贴轨按画面点裁切收齐（item 裁长 + 尾部淡出；D_VOL 恒 1.0 不动）。

## 4. 技术路线（单主线 + 特例线）

### 4.1 主线：video_to_music（唯一常规路线）

- SDK 调用（`pip install elevenlabs`，key 走环境变量 `ELEVENLABS_API_KEY`，纪律见 §6）：
  `client.music.video_to_music(videos=[文件句柄], description=…, tags=[…], model_id="music_v2", output_format=…)`
- 输入上限：1~10 个视频（≤200MB、≤600s，多视频按序拼接）+ `description` + `tags`（≤10 个）。
- **description 长度上限官方口径不一，从严取值**：API reference 写 ≤4100 字符、SDK 2.71.0 docstring 写 ≤1000 字符——**一律按 ≤1000 字符执行**（调查报告勘误 7）。
- **model_id 必须显式传**：API 默认 `music_v1`（UI 默认已是 v2，官方原文称过渡期 API 保持 v1 默认），不传即掉到 v1；现可选 `music_v1 / music_v2 / music_v2_5`，默认用 `music_v2`（调查报告勘误 5）。
- **该端点无任何结构化控制与复现手段**：请求体全字段为 videos / description / tags / model_id / sign_with_c2pa / output_format——无 composition_plan、无 seed、无 store_for_inpainting。每轮生成都是全新抽卡，版本间无血缘（调查报告 Q4）；迭代纪律见 §5。

### 4.2 特例线：compose_music（降格，启用须当单留痕）

**不再是正式生产路线**（2026-10-13 制作人拍板，取代旧版 §4「正式生产路线」定位）。分支启用条件（满足其一才可用；启用时当单交班报告必须注明命中哪条分支与理由）：

- if 纯氛围垫需求（无具体画面对位，视频理解无意义）→ 可用；
- if 主线产物离谱、需甩开画面纯文本生成 → 可用；
- else → 禁用，走主线重抽（§5 第 1 条）。

调用与参数：

- `client.music.compose(prompt=…, music_length_ms=…, model_id="music_v2", force_instrumental=True)`；
- **seed 只能配 composition_plan，禁与 prompt 同用**——官方原文 seed "Cannot be used in conjunction with prompt"（旧版 §4 示例 `compose(prompt=…, seed=…)` 写法违规，作废；调查报告勘误 1）；
- `music.composition_plan.create(prompt=…, music_length_ms=…)` **免费不烧 credits**（只受速率限制），可先出段落计划再人工修订；有 `source_composition_plan` 参数可「以旧 plan 为底改出新 plan」，plan 文本迭代零成本；
- composition_plan v2 结构（调查报告勘误 4 补全）：generation chunk `{"text", "duration_ms", "positive_styles", "negative_styles", "context_adherence"}`；另有 audio reference chunk `{"song_id", "range": {"start_ms", "end_ms"}}`（原曲切片逐样本保留插入）与 conditioning 两字段（`conditioning_ref` / `condition_strength`，low/medium/high/xhigh 四档）——后两者属 inpainting 机制，**仅备案不入主流程**（§5 第 4 条、§7 第 6 条）。

### 4.3 音效生成（补库内无货的冷门 cue）

`client.text_to_sound_effects.convert(text, duration_seconds=0.5~5, loop=False, output_format="mp3_44100_128")`——**5 秒封顶**，只补 one-shot；产物必须标「AI 生成 · 版权档位」进候选池。

### 4.4 台词转写（可选辅助）

`speech_to_text` 330 credits/分钟；**优先本地 Whisper 零成本**。

## 5. 重抽与迭代纪律（2026-10-13 制作人定）

1. **不满意 → 改约束词 → 整首重抽**：主线唯一迭代方式（video_to_music 无 seed/plan/inpainting，见 §4.1）；抽卡成本（900 credits/分钟）制作人确认可接受。
2. **留档**：每轮生成的 description/tags/model_id/产物路径写入交班报告，便于回溯比对；如使用 seed（仅特例线 plan 路径）同样留档。
3. **seed 红线**：官方原文 "exact reproducibility is not guaranteed and outputs may change across system updates"——seed 只是「更一致」，**不得依赖同 seed 重出终版**；终版音质的可靠做法是直接以终版档位（§6 Pro）生成/重生成（调查报告勘误 2；旧版 §5「用同 seed 重出终版」作废）。
4. **inpainting 仅备案、不入主流程**：官方一等能力（生成时 `store_for_inpainting=True` 取 song_id，或 `music.upload` 上传已有音频取 song_id；改造 = 拼「audio reference chunk 保留段 + generation chunk 重生成段」混合 plan 再 compose），机制事实记 §7 第 6 条。**启用须制作人另行拍板**；拍板前一律走第 1 条整首重抽。⚠️ upload 本身按等价生成收费（调查报告 Q3）。

## 6. 版权档位红线

| 档位 | 用途 |
|---|---|
| Free（10k credits/月） | 仅内部测试，**产物禁商用**；⚠️ 实测（2026-10-12 Phase 0/2）：**音效 API 免费档可用，音乐 API 免费档 402 拒绝**（音乐仅网页版免费，API 需付费档） |
| Starter $5/月（30k） | **音乐 API 起点**；商用草稿（MP3 128k；不含流媒体发行音乐本体） |
| Pro $99/月（600k） | PCM 无损 API 输出，终版音质 |

策略：免费档测音效 → 音乐实测需 $5 档（首月 $1，正好含商用授权）→ 终版直接用 $99 档生成/重生成（**不依赖 seed 复现**，见 §5 第 3 条）。每次生成烧 credits（900/分钟，调查报告 Q5 复核无误），**prompt 先打磨再发**；付费凭证（订阅截图/账单）留存。

**API key 纪律**：key 谁用谁配——每台机器的使用者自己设本机环境变量 `ELEVENLABS_API_KEY`（Windows：系统属性→环境变量，或终端 `setx ELEVENLABS_API_KEY "..."` 后重开终端）。**禁止入库、禁止写进工程文件/配置/对话记录、禁止经他人转手**；脚本只读环境变量，取不到即停机报缺。

## 7. API 机制事实（2026-10-13 官方文档核实，纯备案）

> 来源：调查报告（路径见文首修订记录），零生成调用、纯官方文档 + 本机 SDK 2.71.0 核实。本节只记事实，不设流程；流程权威在 §4/§5/§8。

1. 消耗：Music **900 credits/分钟**（官方定价页 HTML 明文核实）；除 plan 建改免费外，**任何产出音频的动作（含 upload）都烧 credits**。
2. video_to_music：无时长参数，时长跟随视频总长；无 plan/seed/inpainting 字段（§4.1）。
3. compose：prompt 与 composition_plan **互斥**；`music_length_ms` 仅配 prompt 使用；时长区间 3000~600000 ms。
4. compose 纯 prompt 路径下服务端**每次生成都会从 prompt 内部建一份 composition plan**，可用 `compose_detailed` 取回（响应含 composition_plan + song_metadata + song_id）（调查报告勘误 8）。
5. 两端点共用同一 `model_id` 枚举（music_v1 / music_v2 / music_v2_5）——可判定同一音乐模型家族、区别在输入条件（视频条件 vs 文本/计划条件）；「区别只在输入源」为推断，官方未明说内部实现（调查报告 Q2）。
6. inpainting 机制（music_v2 / v2_5）：①song_id 入库——生成时 `compose_detailed(..., store_for_inpainting=True)`，或事后 `music.upload(file, extract_composition_plan="music_v2")`（**upload 按等价生成收费**，版权审查不过仍收半价）；②改造 = 混合 plan（audio reference chunk 保留段逐样本不变 + generation chunk 重生成）再 compose；③conditioning：generation chunk 可挂原曲 ≤30s 切片做条件生成；边界：单 chunk 3s~120s、plan ≤30 chunks；保留段跨段过渡靠 context_adherence 平滑，非波形级手术。另有 `music.separate_stems` 分轨分离端点，与修改无关，仅记录存在。

## 8. 产出与贴轨纪律

1. **一集一次只生成一首、只贴一轨**（2026-10-13 制作人拍板）。
2. **废除条款**：「双草稿静音互斥 A/B 贴两轨」施工法**作废**——15v2 双轨贴法系一次性测试处置，不作先例；此后任何一集 BGM 轨只贴一条主线产物，不允许同集并存两条候选 BGM。
3. **职责边界（2026-10-13 制作人拍板调整，取代 10-12 口径）**：音乐总监 = 配乐线自闭环——乐段划分 / 生成 / **BGM 轨贴入归音乐总监**（取代「一切贴轨归见习音效师」旧口径）；库内缺货音效仍只生成不贴轨，音效贴轨归见习音效师。
4. 审美分歧进「待制作人听」清单，生成侧不自裁。

## 9. 工作流接入形态

```
项目开工：风格定调（错峰，不挡流水线）→ foley_project.json.music_style
单集：配乐 brief 三行（风格 tags / 避让对白段 / 乐段划分+秒位）
    → video_to_music 整集一次生成一首（视频+约束词同进，§4.1）→ mp3 落盘任务文件夹
    → 交班报告（生成参数 + 落点建议 + 待制作人听清单）→ 音乐总监贴 BGM 轨一轨（按画面点裁切，§3 第 4 条）
    → 自检（selfcheck 不罩 BGM 轨，单独 volumedetect 终验）
```

- 产物落盘：任务文件夹 `exports\配乐\` 或 `cues\配乐\`（沿用实测口径）。
- 新增命令 `/配乐`（待定，正式接入时立）；**不与 `/贴轨` 混轨**。

## 10. 测试与现状

- Phase 0 已跑（2026-10-12）：连通 PASS，音效 API 免费档可用、音乐 API 免费档 402；Phase 2 双路实测数据留存（video_to_music 产出时长自动对齐视频总长；compose 毫秒级请求误差 0.05s）——详录见 12 号 2026-10-12 节。
- Phase 1（音效双盲对比）未跑，正式接入前补。
- 待办：制作人对既有草稿试听裁决；此后生成一律按 §8 第 1~2 条单首单轨执行。
- Phase 4 决策点不变：质量达标 → 正式接入；不达标 → 归档侦察报告结案。

## 11. 风格 → tags 对照表（初版，实测后扩充）

| 项目风格 | tags 建议 | 描述句式 |
|---|---|---|
| 玄幻古风 | `cinematic, chinese-traditional, guzheng, ethereal, dark-fantasy` | "Xianxia fantasy, traditional Chinese instruments, …" |
| 现代都市 | `modern, urban, ambient, subtle-groove` | "Modern urban drama, restrained, …" |
| 赛博朋克 | `cyberpunk, synthwave, dark-synth, neon` | "Cyberpunk, analog synths, …" |
| 悬疑紧张 | `suspenseful, tension, pulsing, minimal` | "Slow-burn tension, pulsing low-end, …" |

负向约束分支：if 主线（video_to_music）→ tags 无负向位，避让写进 description 句式（如对白段 "no drums, sparse"）；if 特例线（compose_music + composition_plan）→ 用 `negative_styles` 字段。
