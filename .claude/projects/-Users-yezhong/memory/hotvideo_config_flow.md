---
name: 热点视频配置调用流程
description: 热点视频项目完整配置调用链路，修改时一步到位
type: reference
originSessionId: 8aa0ab7a-a118-4ca4-9394-bcc3931aaf53
---
# 热点视频配置调用流程

## 一、配置文件层级关系

```
OpenClaw Gateway
    │
    ├─ ~/.openclaw/workspace/MEMORY.md          ← 工作区记忆（启动时加载，超8000字符截断）
    │
    ├─ ~/.openclaw/workspace/skills/
    │   ├─ auto-hotvideo/auto-hotvideo.yaml    ← 热点视频skill（触发词：热点视频、蹭热点）
    │   └─ bd-wenan/SKILL.md                   ← 病毒文案skill（触发词：写文案）
    │
    └─ youtube-shorts-pipeline/                ← 项目目录
        ├─ state_helper.py                     ← 状态解析（解析用户输入→niche）
        ├─ auto-hotvideo.py                    ← 主入口CLI
        │
        ├─ verticals/
        │   ├─ niche.py                        ← 风格配置加载器
        │   │   ├─ load_niche()                ← 加载 niches/{name}.yaml
        │   │   ├─ get_scene_modes()           ← 获取 scene_modes 配置
        │   │   ├─ get_scene_keywords()        ← 获取场景关键词
        │   │   └─ get_scene_style()           ← 获取场景风格（color/lighting/mood）
        │   │
        │   ├─ draft.py                        ← 文案生成
        │   │   ├─ _load_bd_wenan_framework()  ← 从 ~/.openclaw/workspace/skills/bd-wenan/SKILL.md 加载框架
        │   │   └ generate_draft()            ← 调用LLM生成文案+broll_prompts
        │   │
        │   ├─ broll.py                        ← 图片生成
        │   ├─ tts.py                          ← 语音合成
        │   ├─ captions.py                     ← 字幕生成
        │   ├─ music.py                        ← 音乐选择（NICHE_MUSIC_CONFIG）
        │   └─ assemble.py                     ← 视频合成
        │
        └─ niches/                             ← 风格配置目录
            ├─ general.yaml                    ← 默认风格
            ├─ viral.yaml                      ← 病毒传播（含scene_modes）
            ├─ emotion.yaml                    ← 情感励志
            ├─ business.yaml                   ← 商业风格（含scene_modes）
            ├─ knowledge.yaml                  ← 知识科普
            ├─ horror.yaml                     ← 悬疑恐怖
            ├─ tech.yaml                       ← 科技
            └─ multi_empty_bureau.yaml         ← 多空局
```

## 二、执行流程（用户输入 → 视频生成）

```
用户飞书输入: "文案1/图片3/画面：情感励志风格"
    │
    ▼
【1. 飞书接收】gateway.log: received message
    │
    ▼
【2. Skill激活】auto-hotvideo.yaml triggers匹配
    │
    ▼
【3. 状态解析】state_helper.py parse_user_input()
    │   ├─ 解析素材数量: image_count=3
    │   ├─ 解析切换秒数: switch_seconds
    │   ├─ 解析风格: _parse_chinese_niche("画面：情感励志风格") → emotion
    │   └─ 保存到 ~/.openclaw/memory/auto-hotvideo-state.json
    │
    ▼
【4. 风格加载】niche.py load_niche("emotion")
    │   ├─ 读取 niches/emotion.yaml
    │   ├─ get_scene_modes() → 检查是否有scene_modes
    │   ├─ get_scene_keywords() → 获取场景关键词
    │   └─ get_scene_style() → 获取color/lighting/mood
    │
    ▼
【5. 文案生成】draft.py generate_draft()
    │   ├─ _load_bd_wenan_framework() ← 从bd-wenan/SKILL.md加载病毒文案框架
    │   ├─ get_script_context() ← 从emotion.yaml获取tone/hooks/ctas
    │   ├─ get_visual_context() ← 获取visuals配置
    │   ├─ 调用LLM生成文案
    │   └─ 生成broll_prompts（注入scene_keywords）
    │
    ▼
【6. 图片生成】broll.py generate_broll()
    │   ├─ 调用RunningHub API
    │   └─ 使用prompt_suffix + scene_keywords
    │
    ▼
【7. 语音合成】tts.py generate_voiceover()
    │   └─ 使用niche配置的suggested_voices
    │
    ▼
【8. 字幕生成】captions.py generate_captions()
    │   └─ 使用niche配置的highlight_color/font_size
    │
    ▼
【9. 音乐选择】music.py select_and_prepare_music()
    │   └─ 使用NICHE_MUSIC_CONFIG[niche]
    │
    ▼
【10. 视频合成】assemble.py assemble_video()
    │
    ▼
【11. 飞书回复】dispatch complete
```

## 三、关键配置对应关系

| 用户输入 | 中文风格解析 | YAML配置 | 音乐目录 |
|----------|-------------|----------|----------|
| 画面：情感励志风格 | emotion | niches/emotion.yaml | music/emotion/ |
| 画面：商业风格 | business | niches/business.yaml | music/viral/ |
| 画面：病毒传播 | viral | niches/viral.yaml | music/viral/ |
| 画面：科技风格 | tech | niches/tech.yaml | music/tech/ |
| 风格:viral | viral | niches/viral.yaml | music/viral/ |

## 四、常见问题排查

### 问题1: 文案质量低/重复
- 检查: `_load_bd_wenan_framework()` 是否正确加载 SKILL.md
- 修复: 确保 ~/.openclaw/workspace/skills/bd-wenan/SKILL.md 存在

### 问题2: 图片风格不对
- 检查: `get_scene_keywords()` 是否返回关键词
- 修复: 确保 niches/{niche}.yaml 有 scene_modes 配置

### 问题3: 音乐不匹配
- 检查: NICHE_MUSIC_CONFIG 是否有对应niche
- 修复: 在 music.py 添加配置

### 问题4: 风格解析失败
- 检查: state_helper.py 的 CHINESE_NICHE_MAP
- 修复: 添加新的中文风格映射

## 五、修改时一步到位清单

修改任何功能时，必须检查以下关联文件：

| 修改目标 | 需要同步修改的文件 |
|----------|-------------------|
| 新增风格 | niches/{name}.yaml + music.py NICHE_MUSIC_CONFIG + state_helper.py CHINESE_NICHE_MAP + valid_niches |
| 修改文案框架 | bd-wenan/SKILL.md（draft.py会自动读取） |
| 修改场景模式 | niches/{name}.yaml 的 scene_modes + niche.py 的读取函数 |
| 修改字幕样式 | niches/{name}.yaml 的 captions 部分 |
| 修改音乐 | music/{niche}/ 目录 + music.py NICHE_MUSIC_CONFIG |

## 六、日志关键时间点

| 日志关键词 | 含义 |
|-----------|------|
| `received message` | 收到飞书消息 |
| `dispatching to agent` | 开始处理 |
| `dispatch complete` | 处理完成 |
| `typing TTL reached` | 输入指示器超时（2分钟无输出） |
| `embedded run timeout` | 执行超时（10分钟） |
| `reconnect` | WebSocket重连 |