# auto-hotvideo — 蹭热点视频生成工具

独立的短视频生成工具，供Claude Code/OpenClaw等AI工具调用。

## 快速开始

```bash
cd /Users/yezhong/youtube-shorts-pipeline
pip install -r requirements.txt
```

## 配置

编辑 `~/.verticals/config.json`:

```json
{
  "RUNNINGHUB_API_KEY": "your_key",
  "DASHSCOPE_API_KEY": "your_key",
  "XUNFEI_API_KEY": "your_key",
  "TTS_PROVIDER": "dashscope",
  "LLM_PROVIDER": "xunfei"
}
```

## 用法

```bash
# 查看今日热点
python auto-hotvideo.py hot

# JSON格式输出（供AI工具解析）
python auto-hotvideo.py hot --json --limit 5

# 指定主题生成视频
python auto-hotvideo.py make "一人公司"

# 使用视频API生成动态场景（每2秒切换场景）
python auto-hotvideo.py make "一人公司" --video

# 全自动：获取今日热点并生成视频
python auto-hotvideo.py run

# 全自动 + 视频API
python auto-hotvideo.py run --video
```

## 输出

- 视频文件：`~/.verticals/media/verticals_{job_id}_zh.mp4`
- 草稿文件：`~/.verticals/drafts/{job_id}.json`

## 费用

- 图片生成：$0.05/张
- 视频生成：$0.2/8秒
- TTS：按字符计费

## AI工具调用示例

OpenClaw/Claude Code可以这样调用：

```python
import subprocess
import json

# 获取热点
result = subprocess.run(
    ["python", "auto-hotvideo.py", "hot", "--json", "--limit", "5"],
    capture_output=True, text=True, cwd="/Users/yezhong/youtube-shorts-pipeline"
)
topics = json.loads(result.stdout)

# 生成视频
result = subprocess.run(
    ["python", "auto-hotvideo.py", "make", topics[0]["title"], "--video", "--json"],
    capture_output=True, text=True, cwd="/Users/yezhong/youtube-shorts-pipeline"
)
video_info = json.loads(result.stdout)
print(f"视频已生成: {video_info['video_path']}")
```

---

# Verticals v3 (原项目)

**The open source AI content engine with built-in niche intelligence.**

> Topic in. Published Short out. Any niche. ~$0.11 per video.

```
python -m verticals run --topic "Sam Altman just mass-fired 200 safety researchers" --niche tech
```

## CLI Commands

### Full pipeline
```bash
python -m verticals run --topic "headline" --niche tech
python -m verticals run --topic "headline" --niche cooking --provider ollama
python -m verticals run --discover --niche gaming --auto-pick
```

### Individual stages
```bash
python -m verticals draft --topic "headline" --niche tech
python -m verticals produce --draft <path> --lang en
python -m verticals upload --draft <path> --platform youtube
python -m verticals topics --niche tech --limit 20
python -m verticals hot --list  # 今日热点
```

## Provider Support

### LLM (script generation)
| Provider | Cost | Setup |
|----------|------|-------|
| Claude | ~$0.02/script | `ANTHROPIC_API_KEY` |
| Gemini | Free tier | `GEMINI_API_KEY` |
| GPT | ~$0.01/script | `OPENAI_API_KEY` |
| Ollama | Free | Install Ollama |
| 讯飞 | 按量计费 | `XUNFEI_API_KEY` |
| DashScope | 按量计费 | `DASHSCOPE_API_KEY` |

### TTS (voiceover)
| Provider | Cost | Notes |
|----------|------|-------|
| Edge TTS | Free | 300+ voices |
| ElevenLabs | ~$0.05/video | Premium |
| DashScope CosyVoice | 按量计费 | 中文情感语音 |

### Visuals (b roll)
| Provider | Cost | Notes |
|----------|------|-------|
| RunningHub | $0.05/image | AI生成图片 |
| RunningHub Video | $0.2/8s | AI生成视频 |
| Pexels | Free | Stock footage |

## Cost Per Video

| Configuration | Cost |
|---------------|------|
| Premium (Claude + RunningHub + ElevenLabs) | ~$0.15 |
| Budget (DashScope + RunningHub + CosyVoice) | ~$0.10 |
| Free (Ollama + Pexels + Edge TTS) | $0.00 |

## License

MIT
