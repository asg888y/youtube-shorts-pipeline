---
name: Pipeline quality & workflow standards
description: 质量标准、流程规范、每日启动检查清单 — 禁止降级、禁止反复调试
type: feedback
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---

## 质量标准（不可降级）

### 素材
- **图片提示词**：必须由 LLM 根据文案内容生成，场景/色调/光线差异化。禁止模板复制。
- **素材充足**：G7 门禁 — 图片 < max(3, 时长/15+1) 张就停止，不产垃圾。
- **图片 API**：Suchuang nanobanana2 并发慢（首张 60s，后续 600s+）。可换 API，不要降低素材数量要求。
- **视频素材**：只收竖屏(9:16)，横屏直接丢弃。

### 音频
- **TTS**：CosyVoice-v3-plus + longanyang(男)/longanhuan(女)，emotion 仅 fearful/angry/sad。
- **质检**：G1-G6 全部 enforce，不过就停。G3(BGM)必须拦截。

### 字幕
- 字号≤8，Bold=0，Outline=1.5，PingFang SC
- 每行≤10 字，禁止单 cue 多行
- 标点符号靠前一行（不孤悬）

### 配置
- 管线启动前 validate_config() 校验 API key / 模型名 / OCR 参数
- 启动时清洗 selection.json 中非法 emotion（"neutral"→fearful）

## 每日启动流程

1. 读 MEMORY.md
2. 读本文件
3. 找今日文案（`projects/` 下当天日期的 wenan）
4. 用管线生产：`python pipeline.py projects/<日期_主题>`
5. 质检全部通过 → 打开目录确认成品
6. 保存当天工作结果到 memory

## 禁止事项

- ❌ 图片提示词用模板（必须 LLM 生成）
- ❌ 素材不够硬跑（G7 不过就是不过）
- ❌ API 挂了反复调试（上限 1 次尝试，失败了换方案）
- ❌ 同一个 bug 反复修（修完立即更新本文件）
- ❌ 不读记忆就动手
- ❌ 未经审批擅自创作新内容

## Why

用户反复看到同样的错误被"修复"多次。token 被浪费在重复调试上。质量标准是铁律，不是建议。
