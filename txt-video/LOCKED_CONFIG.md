# 🔒 锁死配置 - 禁止修改

**唯一授权修改方式：用户书面确认"同意"**

---

## 锁死声明

**所有核心文件已锁死，OpenClaw激活后无法介入修改。**

---

## 锁死的文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `render.js` | 🔒 锁死 | 主程序入口 |
| `Root.tsx` | 🔒 锁死 | Remotion配置 |
| `src/style-1-black.tsx` | 🔒 锁死 | 唯一风格组件 |
| `api/tts.js` | 🔒 锁死 | TTS模块 |
| `api/image.js` | 🔒 锁死 | 图片模块 |

---

## 锁死的风格

**唯一风格**: `style-1-black` → `Style1Black`

其他风格（style-2-art, style-3-gradient）已禁用。

---

## 锁死的参数（render.js）

```javascript
const LOCKED_PROPS = {
  backgroundOpacity: 0.6,    // 背景透明度
  titleSize: 80,             // 主标题字号
  subtitleSize: 42,          // 副标题字号
  contentTop: "28%",         // 内容区域顶部位置
  audioFile: "voiceover.wav", // 音频文件名
  backgroundImage: "bg1.png", // 背景图片名
};

// 风格强制锁定
const compositionId = 'Style1Black';
```

---

## 锁死的文案格式

**完整格式**（每行一段）：
```
关键词|主标题|副标题|引用
```

**示例**：
```
学习误区|跟大师学三年|不如看书家书|一次成功案例是精心包装的序数
成功陷阱|成功者的框架|是七点|有太多因素被隐去
```

---

## 素材库

**位置**: `public/assets/backgrounds/style-1-black/`

**背景图片** (随机选择):
| 文件 | 说明 |
|------|------|
| bg1.png | 素材库图片 |
| bg10.png | 素材库图片 |
| bg11.png | 素材库图片 |
| bg16.png | 素材库图片 |
| bg17.png | 素材库图片 |
| bg18.png | 素材库图片 |
| bg21.png | 素材库图片 |
| bg48.png | 素材库图片 |
| bg60.png | 素材库图片 |
| bg62.png | 素材库图片 |

**随机机制**: 每次渲染自动从素材库随机选择一张背景图

---

## 锁死的输出规格

- 分辨率: 1080×1920 (竖屏)
- 帧率: 30fps
- 编码: H.264 + AAC
- 质量: 80%

---

## 自动化流程

OpenClaw激活后：
1. 读取文案输入
2. 自动解析为分段格式
3. 调用百炼TTS生成语音
4. Remotion渲染视频
5. 输出视频文件

**全程无需人工介入，格式100%锁定。**

---

## 禁止事项

- ❌ 禁止修改 LOCKED_PROPS 参数
- ❌ 禁止修改 Root.tsx Composition
- ❌ 禁止修改 style-1-black.tsx 样式
- ❌ 禁止切换风格
- ❌ 禁止修改 TTS 音色
- ❌ 禁止修改文案解析格式

---

**锁定时间**: 2026-05-13
**锁定人**: 用户
