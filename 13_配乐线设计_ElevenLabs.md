# 13 · 配乐线设计（ElevenLabs 接入）

> 状态：设计定稿，待实测（卡账号注册）。本册是配乐线的**设计权威**；实测后结论回写本册并记 12 号。
> 音效侧规矩全部沿用（NAS 只读 / 并发 ≤2 / D_VOL 不动 / 脚步不配），配乐是**独立工种**，不进 `/贴轨`。

## 1. 定位与分工（2026-10-12 制作人定调）

- 配乐目标：**进成片**，一集（约 1 分钟）1~2 个乐段，3 段罕见——按「乐段」不按「首」。
- **分工**：ElevenLabs 模型负责理解视频内容/情绪（省我方 token 与时间）；我方只出**风格 + 硬约束**。
- 冲突处置：我方分析为权威（可审、有证据），对方为黑盒（结论不可见，只体现于产物）；冲突时按我方口径重生成，分歧上报制作人；终版路线（compose_music）对方不看视频，结构零冲突。审美终审权 = 制作人耳朵。

## 2. 风格两级制（先验 ≠ 标准）

| 层级 | 内容 | 性质 |
|---|---|---|
| 项目级风格 | 开工前错峰做：抽 2~3 集代表集（首/中/高潮）粗看定整体风格 → 写进 `foley_project.json` 的 `music_style` 字段（风格名 + tags + 描述句式） | 先验，可推翻 |
| 单集基调 | 默认继承项目风格；只写乐段划分 + 避让对白段 + 偏离检查 | 继承或覆盖 |
| 段级现实 | 画面内容优先于标签（古风剧里穿越者掏枪 = 该段切现代/混搭，不强行古风）——与选材「声源存在性」同哲学：标签是降权不是禁区 | 硬约束 |

偏离检测问法：「这段的画面还属于项目风格吗」——分析师动作报告里看得见答案。

## 3. 时长规则（2026-10-12 制作人定）

1. 乐段时长**由我方按画面段落算死**（起点~终点，精确到秒）；
2. 生成请求时长 = 判断时长 **+15% 且至少 +2 秒**（容错余量，宁长勿短）；
3. 贴轨按画面点裁切收齐（item 裁长 + 尾部淡出；D_VOL 恒 1.0 不动）。

## 4. 技术路线（官方 MCP 源码核实 2026-10-12）

| | 正式生产 `compose_music` | 草稿/提案 `video_to_music` |
|---|---|---|
| 看视频 | 不看（零冲突） | 看（server 端拼接，配乐长度对齐视频总时长） |
| 时长 | `music_length_ms` 毫秒级 / composition_plan 分段 | 无参数，跟随视频 |
| 输入 | `prompt` 或 `composition_plan`（二选一） | 1~10 视频（≤200MB、≤600s）+ `description`（≤4100 字符）+ `tags`（≤10 个） |

- SDK 调用（`pip install elevenlabs`，key 走环境变量 `ELEVENLABS_API_KEY`）：
  - `client.music.compose(prompt=…, music_length_ms=…, model_id="music_v2", force_instrumental=True, seed=…)`
  - `client.music.composition_plan.create(prompt=…, music_length_ms=…)`——**免费**（不烧 credits，只受速率限制），用来先出段落计划再人工修订
  - composition_plan v2 结构：`{"chunks": [{"text", "duration_ms", "positive_styles", "negative_styles", "context_adherence"}, ...]}`
  - `client.music.video_to_music(videos=[文件句柄], description=…, tags=[…], model_id="music_v2")`
- 音效生成（补库内无货的冷门 cue）：`client.text_to_sound_effects.convert(text, duration_seconds=0.5~5, loop=False, output_format="mp3_44100_128")`——**5 秒封顶**，只补 one-shot；产物必须标「AI 生成 · 版权档位」
- 台词转写（可选辅助）：`speech_to_text` 330 credits/分钟；**优先本地 Whisper 零成本**

## 5. 版权档位红线

| 档位 | 用途 |
|---|---|
| Free（10k credits/月） | 仅内部测试，**产物禁商用** |
| Starter $5/月（30k） | 商用草稿（MP3 128k；不含流媒体发行音乐本体） |
| Pro $99/月（600k） | PCM 无损 API 输出，终版音质 |

策略：免费档测试 → $5 档出草稿定方向 → 定稿后按需升级 $99 用同 `seed` 重出终版。每次生成烧 credits（900/分钟），**prompt 先打磨再发，禁止当抽卡机**。付费凭证（订阅截图/账单）留存。

## 6. 工作流接入形态

```
项目开工：风格定调（错峰，不挡流水线）→ foley_project.json.music_style
单集：配乐 brief 三行（风格 tags / 避让段 / 乐段划分+时长含余量）
    → compose_music 生成 → mp3 落盘任务文件夹
    → 贴 BGM 轨组（36~40），标「AI 草稿 · 待替换」，按画面点裁切
    → 随工程一并自检（selfcheck 不罩 BGM 轨，单独 volumedetect 终验）
```

- 新增命令 `/配乐草稿`（待定，实测后立）；**不与 `/贴轨` 混轨**。
- 产物落盘：任务文件夹 `exports\配乐\` 或 `cues\配乐\`（实测时定，写回本节）。

## 7. 测试计划（拿到 key 后按序）

- Phase 0：`scripts\elevenlabs_probe.py` 连通自测（key 有效性 + 出一条 2s 音效 + 余额读回）
- Phase 1：音效对比——3~5 个真实 case（含 1 个库内检索失败的冷门音效，如 glitch），双盲对比
- Phase 2：配乐实测——14-1v2 成片：①整集 video_to_music 一条（快捷路）②按乐段 compose_music 两条（精确路，含 +15% 余量）；对照分析师报告情绪点逐段评分：贴合度/时长偏差/起落位置/对白避让
- Phase 3（顺手）：speech_to_text 说话人分离审素材
- Phase 4 决策点：质量达标 → $5 档上车接入；不达标 → 归档侦察报告结案

## 8. 风格 → tags 对照表（初版，实测后扩充）

| 项目风格 | tags 建议 | 描述句式 |
|---|---|---|
| 玄幻古风 | `cinematic, chinese-traditional, guzheng, ethereal, dark-fantasy` | "Xianxia fantasy, traditional Chinese instruments, …" |
| 现代都市 | `modern, urban, ambient, subtle-groove` | "Modern urban drama, restrained, …" |
| 赛博朋克 | `cyberpunk, synthwave, dark-synth, neon` | "Cyberpunk, analog synths, …" |
| 悬疑紧张 | `suspenseful, tension, pulsing, minimal` | "Slow-burn tension, pulsing low-end, …" |

（负向约束用 composition_plan 的 `negative_styles`，如对白段 "no drums, sparse"。）
