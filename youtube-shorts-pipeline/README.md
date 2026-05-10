# auto-hotvideo — 蹭热点视频生成工具

独立的短视频生成工具，供Claude Code/OpenClaw等AI工具调用。

## 快速开始

```bash
cd /Users/yezhong/youtube-shorts-pipeline
pip install -r requirements.txt
```

## 配置

API密钥使用 **macOS Keychain** 安全存储，不再使用明文配置文件。

```bash
# 设置密钥（首次配置）
python3 -m verticals.keychain_manager set DASHSCOPE_API_KEY your_key
python3 -m verticals.keychain_manager set RUNNINGHUB_API_KEY your_key

# 查看密钥状态
python3 -m verticals.keychain_manager list

# 迁移旧配置中的密钥
python3 -m verticals.keychain_manager migrate
```

## 用法

```bash
# 查看今日热点
python auto-hotvideo.py hot

# JSON格式输出（供AI工具解析）
python auto-hotvideo.py hot --json --limit 5

# 指定主题生成视频
python auto-hotvideo.py make "一人公司"

# 指定画面风格
python auto-hotvideo.py make "情感话题" --niche emotion

# 使用视频API生成动态场景
python auto-hotvideo.py make "一人公司" --video

# 全自动：获取今日热点并生成视频
python auto-hotvideo.py run
```

## 画面风格（--niche）

| 风格名 | 显示名 | 文案风格 | 画面风格 | 适用场景 |
|--------|--------|----------|----------|----------|
| `general` | 通用 | 清晰、对话式 | 电影感、专业 | 通用内容 |
| `viral` | 病毒传播 | 震撼、悬念、冲击 | 高对比、动态 | 热点、争议话题 |
| `emotion` | 情感励志 | 温暖、治愈、共鸣 | 柔和、电影感 | 情感、人性洞察 |
| `knowledge` | 知识科普 | 专业、清晰、有趣 | 信息可视化 | 干货、科普 |
| `horror` | 悬疑惊悚 | 神秘、紧张、悬念 | 暗色调、高对比 | 悬疑、惊悚 |
| `tech` | 科技 | 专业、观点鲜明 | 简洁、暗色、霓虹 | 科技、AI |
| `multi_empty_bureau` | 多空情报局 | 专业、冷静、深度 | 情报室/HUD/军事地图 | 地缘政治、金融 |

**OpenClaw 飞书输入示例：**
```
热点视频 风格:emotion
文案1/图片3，切换3秒/，画面：情感励志风格
```

## 标准文案输入格式

### 格式1：直接输入文案（推荐）

```
文案：你的文案内容在这里 /图片3/视频1 切换2秒 风格:business
```

**解析规则**：
- `文案：` 或 `文案:` 开头表示直接输入文案
- `/图片N` 指定图片数量
- `/视频N` 指定视频片段数量
- `切换N秒` 指定每个素材展示时长（支持小数，如`切换2.5秒`）
- `风格:xxx` 或 `画面：xxx风格` 指定画面风格

**完整示例**：
```
文案：合法性的溢价，是留给后来者的门票。真正的门槛从来不是能力，而是入场券。/图片4 切换2秒 风格:business
```

### 格式2：选择热点生成

```
3 切换3秒 图片5 风格:viral
```

**解析规则**：
- 纯数字选择对应编号的热点
- 其他参数同上

### 格式3：视频链接转录

```
https://视频链接 /图片3 切换2秒 风格:emotion
```

**解析规则**：
- 以http开头识别为视频链接
- 自动转录视频中的语音为文案

### 可用风格列表

| 风格代码 | 中文别名 | 适用场景 |
|----------|----------|----------|
| `general` | 通用、一般 | 默认风格 |
| `viral` | 病毒、传播、震撼、冲击 | 热点争议话题 |
| `emotion` | 情感、励志、温暖、治愈 | 情感内容 |
| `knowledge` | 知识、科普、专业 | 干货科普 |
| `horror` | 恐怖、悬疑、惊悚 | 悬疑内容 |
| `tech` | 科技、技术、未来 | 科技AI |
| `business` | 商业、财富、奢华 | 商业内容 |

### 参数默认值

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 图片数量 | 3 | 未指定时默认3张 |
| 视频数量 | 0 | 未指定时不生成视频 |
| 切换时长 | 2秒 | 未指定时默认2秒 |
| 风格 | general | 未指定时使用通用风格 |

## 参数解析说明

### 用户输入格式
系统支持多种参数组合格式：

1. **选择热点**：纯数字选择对应编号的热点（如"3"选择第3个热点）
2. **自定义参数**：
   - `切换3秒`：设置场景切换时长为3秒
   - `图片5`：生成5张B-roll图片
   - `视频2`：生成2个动态视频片段
   - `开头视频`：开头使用视频片段
   - `风格:emotion`：指定画面风格
3. **组合使用**：`"3 切换3秒 视频2 风格:viral"`

### 素材补充机制
当API生成失败或指定使用历史素材时，按以下顺序补充：

1. **首选**：RunningHub API生成
2. **备选1**：本地历史素材库（`local_assets/images/`）
3. **备选2**：纯色背景（保证视频完整性）

## 文案质量提升

系统集成了 **bd-wenan 病毒文案框架**，自动应用以下规则：

### 情绪钩子（开头12字内必须触发一种）
- 恐惧型："你再不___，就会___"
- 反差型："你以为___，其实___"
- 归属型："这说的就是你"
- 好奇型："90%的人不知道___"
- 愤怒型："凭什么___"

### 金句创作（每个文案至少2个）
- 8-18字，包含对比或矛盾
- 具备独立传播能力

### 5段式结构
| 段落 | 时长 | 目标 |
|------|------|------|
| 开头 | 0-3秒 | 一句话让人停下来 |
| 承接 | 3-10秒 | 让用户觉得"说的就是我" |
| 转折 | 10-20秒 | 建立信任，输出金句 |
| 干货 | 20-35秒 | 给用户能带走的东西 |
| 结尾 | 35-45秒 | 让人想转发 |

### 评论区钩子
文案末尾自动预埋3个钩子引导互动。

## 生图提示词优化

情感励志类（emotion）和病毒传播类（viral）风格自动添加：
- **中国人面孔、亚洲人特征**
- 避免：外国人面孔、欧美人特征

确保画面有代入感。

## 费用

- 图片生成：¥0.05/张
- 视频生成：¥0.2/8秒
- TTS：按字符计费（DashScope CosyVoice）

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

# 生成视频（指定风格）
result = subprocess.run(
    ["python", "auto-hotvideo.py", "make", topics[0]["title"], "--niche", "emotion", "--json"],
    capture_output=True, text=True, cwd="/Users/yezhong/youtube-shorts-pipeline"
)
video_info = json.loads(result.stdout)
print(f"视频已生成: {video_info['video_path']}")
```

## 相关文档

- [成本审批机制.md](成本审批机制.md) - API调用审批流程
- [质量标准与良品率.md](质量标准与良品率.md) - 视频质量标准
- [任务恢复机制.md](任务恢复机制.md) - 断点续传
- [模型锁定说明.md](模型锁定说明.md) - 成本控制

---

# Verticals v3 (原项目)

**The open source AI content engine with built-in niche intelligence.**

> Topic in. Published Short out. Any niche. ~¥0.10 per video.

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
| MiniMax | 按量计费 | `MINIMAX_API_KEY` |

### TTS (voiceover)
| Provider | Cost | Notes |
|----------|------|-------|
| DashScope CosyVoice | 按量计费 | 中文情感语音（唯一TTS） |

### Visuals (b roll)
| Provider | Cost | Notes |
|----------|------|-------|
| RunningHub | ¥0.05/image | AI生成图片 |
| RunningHub Video | ¥0.2/8s | AI生成视频 |

## License

MIT
