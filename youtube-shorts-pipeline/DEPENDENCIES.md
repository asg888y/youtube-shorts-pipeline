# 项目依赖关系

> ⚠️ 修改任何文件前必须先读取此文件，确认影响范围

## 项目信息

- **名称**: youtube-shorts-pipeline
- **路径**: `/Users/yezhong/youtube-shorts-pipeline`
- **GitHub**: https://github.com/asg888y/youtube-shorts-pipeline
- **功能**: 蹭热点视频生成工具

---

## 调用方

| 调用方 | 路径 | 调用方式 |
|--------|------|----------|
| OpenClaw | `~/.openclaw/workspace/skills/auto-hotvideo/` | SKILL.md |
| Claude Code | `~/.claude/skills/auto-hotvideo.md` | skill文件 |

---

## 核心文件

| 文件 | 功能 | 修改影响 |
|------|------|----------|
| `auto-hotvideo.py` | 主CLI入口 | 全链路 |
| `state_helper.py` | 状态管理 | 多轮会话 |
| `verticals/assemble.py` | 视频合成 | 输出质量 |
| `verticals/broll.py` | 图片生成 | RunningHub调用 |
| `verticals/tts.py` | 语音合成 | CosyVoice调用 |
| `verticals/llm.py` | LLM调用 | 脚本生成 |
| `verticals/captions.py` | 字幕生成 | Whisper调用 |

---

## 外部依赖

| 依赖 | 版本/路径 | 用途 |
|------|-----------|------|
| ffmpeg-full | `/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg` | 视频合成+字幕烧录 |
| RunningHub API | `https://www.runninghub.cn/openapi/v2/` | 图片/视频生成 |
| DashScope API | CosyVoice TTS | 语音合成 |
| Whisper | 本地 | 字幕时间戳 |

---

## 配置文件

| 文件 | 路径 | 内容 |
|------|------|------|
| API密钥 | `~/.verticals/config.json` | RUNNINGHUB_API_KEY, DASHSCOPE_API_KEY |
| 内容风格 | `niches/*.yaml` | viral, tech, general |

---

## 修改检查清单

修改前确认：

- [ ] 读取此文件了解影响范围
- [ ] 检查调用方SKILL.md是否需要同步更新
- [ ] 检查Claude Code skill是否需要同步更新
- [ ] 测试修改后功能正常
- [ ] 提交并推送到GitHub

---

## 最近修改记录

| 日期 | 文件 | 修改内容 |
|------|------|----------|
| 2026-05-08 | verticals/llm.py | MiniMax M2.7 Anthropic兼容接口 |
| 2026-05-08 | auto-hotvideo.py | 使用ffmpeg-full替代标准ffmpeg |
| 2026-05-08 | auto-hotvideo.py | 修复switch_seconds参数无效 |
| 2026-05-07 | broll.py | RunningHub OpenAPI v2端点 |
