# 本地素材库结构

## 目录结构

```
local_assets/
├── images/           # 图片素材
│   ├── general/      # 通用素材
│   │   ├── broll_0.png
│   │   ├── broll_1.png
│   │   └── broll_2.png
│   ├── viral/        # 病毒传播风格（高对比、冲击力）
│   ├── emotion/      # 情感励志风格（温暖、治愈）
│   ├── knowledge/    # 知识科普风格（专业、清晰）
│   ├── horror/       # 悬疑惊悚风格（暗色调、神秘）
│   └── tech/         # 科技风格（现代、科技感）
├── videos/           # 视频素材
│   ├── general/
│   ├── viral/
│   ├── emotion/
│   ├── knowledge/
│   ├── horror/
│   └── tech/
├── audio/            # 音频素材
└── music/            # 背景音乐
```

## 素材加载优先级

当 API 生成失败或用户指定使用本地素材时，系统按以下顺序加载：

1. **风格素材** (`local_assets/images/{niche}/`)
   - 根据当前视频风格加载对应目录
   - 例如：`--niche viral` → 加载 `viral/` 目录素材

2. **历史生成素材** (`~/.verticals/media/work_*/`)
   - 从最近生成的工作文件夹提取
   - 最多检查5个最近文件夹

3. **风格颜色素材** (`standard_assets/images/colors/`)
   - 根据风格选择合适的纯色背景
   - viral: 红色系
   - emotion: 蓝紫色系
   - knowledge: 蓝灰色系
   - horror: 暗色系
   - tech: 科技蓝

4. **通用素材** (`local_assets/images/general/`)
   - 回退到通用素材目录

5. **动态生成背景**
   - 根据风格生成对应色调的纯色背景

## 添加新素材

### 方式1：手动添加

```bash
# 将素材放入对应风格目录
cp my_image.png local_assets/images/viral/
```

### 方式2：从历史生成复制

```bash
# 查看最近生成的素材
ls ~/.verticals/media/work_*/broll_*.png

# 复制到风格目录
cp ~/.verticals/media/work_1778302922/broll_*.png local_assets/images/viral/
```

### 素材命名规范

- 图片：`broll_0.png`, `broll_1.png`, `broll_2.png` ...
- 视频：`clip_0.mp4`, `clip_1.mp4` ...
- 音频：`bgm_0.mp3`, `sfx_0.mp3` ...

## 风格素材特点

| 风格 | 色调 | 内容特点 | 示例 |
|------|------|----------|------|
| viral | 高对比、鲜艳 | 冲击力强、动态感 | 爆炸效果、对比图 |
| emotion | 暖色调、柔和 | 温暖、治愈 | 日落、人物特写 |
| knowledge | 蓝灰色、清晰 | 专业、信息可视化 | 图表、示意图 |
| horror | 暗色调、神秘 | 压抑、悬疑 | 阴影、空旷场景 |
| tech | 科技蓝、现代 | 未来感、科技感 | 电路、数据流 |

## 使用示例

```bash
# 使用病毒传播风格
python3 auto-hotvideo.py make "主题" --niche viral

# 使用情感励志风格 + 本地素材
python3 auto-hotvideo.py make "主题" --niche emotion --use-local

# OpenClaw 用户输入
"热点视频 风格:horror"
"3 风格:knowledge 图片5"
```
