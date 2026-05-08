---
name: TTS production config
description: CosyVoice-v3-plus 自有TTS唯一配置 — 模型/音色/情感/参数硬限制
type: project
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
# TTS 生产配置（自有百炼API，禁止任何付费TTS）

## 硬限制

| 参数 | 允许值 | 默认值 |
|------|--------|--------|
| 模型 | `cosyvoice-v3-plus` | — |
| 男声 | `longanyang` | 主力 |
| 女声 | `longanhuan` | 可用 |
| 情感 | `fearful` / `angry` / `sad` | `fearful` |
| 语速 | 1.0 ~ 1.3 | **1.3（默认），情绪低落/悲伤文案用1.0** |
| 音高 | 0.5 ~ 2.0 | 0.85 |
| 音量 | 0 ~ 100 | 55 |
| 场景 | `脱口秀表演` | — |
| Instruct格式 | `你正在进行脱口秀表演，你说话的情感是<emotion>。` | — |

## 语速规则

- **默认 1.3x** — 所有常规内容，快节奏病毒传播
- **1.0x（原速）** — 仅悲伤/低落/催泪类文案，用慢速增强情绪感染力

## 禁止

- CosyVoice-v3-plus 仅支持 3 个系统音色，其他 v3-flash 音色一律 418 错误
- 禁止自由 instruct（428 错误），只能用标准格式
- 禁止使用任何付费TTS服务
- 禁止其他情感值
- 禁止语速超出 1.0-1.3 范围

## API

- 服务: 百炼 DashScope
- Key: base64编码存储在 `~/.claude/memory/tools_resources_and_taboos.md`
- 计费: 2元/万字符

## 代码位置

- 库: `~/video_creator/lib/tts_client.py`
- Pixelle: `~/pixelle_project/scheme_a/pipeline/api_client.py`
- 配置: `~/video_creator/lib/config.py`
- 技能: `~/.claude/skills/audio-skill/SKILL.md`
