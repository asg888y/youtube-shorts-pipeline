---
name: 视频转录工具配置
description: 抖音/TikTok等短视频平台视频转录工具和API配置
type: reference
originSessionId: a425339a-241d-4248-bd18-46b4039d93b8
---
## 视频转录工具配置

### 下载工具（多备选方案）

| 优先级 | 工具 | 安装命令 | 支持平台 |
|--------|------|----------|----------|
| 1 | yt-dlp | `pip install yt-dlp` | 抖音、TikTok、B站、YouTube、快手、小红书 |
| 2 | gallery-dl | `pip install gallery-dl` | 抖音、TikTok、B站 |
| 3 | TikTokApi | `pip install TikTokApi` | 抖音、TikTok |
| 4 | streamlink | `pip install streamlink` | YouTube、B站 |

### 转录API（多备选方案）

| 优先级 | API | 地址 | 说明 |
|--------|-----|------|------|
| 1 | 自建Whisper | http://8.138.165.244:80/whisper/v1/audio/transcriptions | 免费、快速、tiny模型 |
| 2 | OpenAI Whisper | https://api.openai.com/v1/audio/transcriptions | 需API密钥 |
| 3 | faster-whisper | 本地 | 无需网络、tiny模型 |

### 使用方法

```python
from verticals.video_transcriber import transcribe_video

result = transcribe_video("https://www.douyin.com/video/123456")

if result['success']:
    print(f"文案: {result['transcript']}")
    print(f"时长: {result['duration']}秒")
    print(f"方法: {result['method']}")
```

### 相关文件

- `verticals/video_transcriber.py`: 主转录工具
- `verticals/link_extractor.py`: 链接内容提取器

### Why

抖音等短视频平台视频转录需要多个备选方案，因为：
1. 平台API经常变化
2. 单一工具可能失效
3. 需要确保高可用性

### How to apply

系统会自动按优先级尝试多个下载器和转录API，确保转录成功率。
