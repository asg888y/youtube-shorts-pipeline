---
name: OpenClaw进度输出机制
description: 解决typing indicator 2分钟超时问题，让agent持续显示工作状态
type: reference
originSessionId: 8aa0ab7a-a118-4ca4-9394-bcc3931aaf53
---
# OpenClaw 进度输出机制

## 问题根因

OpenClaw的typing indicator（飞书"正在输入..."表情）有**硬编码的2分钟超时**：
- 代码位置：`openclaw/dist/auth-profiles-DRjqKE3G.js`
- 硬编码值：`typingTtlMs = 2 * 6e4`（120秒）

当agent执行长时间任务（如写文案、调用API）超过2分钟时，typing indicator会自动停止，用户无法判断agent是否还在工作。

---

## 长期方案1：添加 `typingTtlSeconds` 配置选项（已实施）

### 修改内容

修改了OpenClaw源码，添加 `typingTtlSeconds` 配置支持：

**修改的文件：**
- `/Users/yezhong/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/dist/auth-profiles-DRjqKE3G.js`
- `/Users/yezhong/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/dist/auth-profiles-DDVivXkv.js`
- `/Users/yezhong/.nvm/versions/node/v22.22.2/lib/node_modules/openclaw/dist/reply-Bm8VrLQh.js`

**修改内容：**
```javascript
// 添加配置读取
const configuredTypingTtlSeconds = agentCfg?.typingTtlSeconds ?? sessionCfg?.typingTtlSeconds;
const typingTtlMs = (typeof configuredTypingTtlSeconds === "number" ? configuredTypingTtlSeconds : 120) * 1e3;

// 传递给createTypingController
const typing = createTypingController({
  ...
  typingTtlMs,
  ...
});
```

### 配置方法

在 `openclaw.json` 中添加：

```json
{
  "agents": {
    "defaults": {
      "typingIntervalSeconds": 6,
      "typingTtlSeconds": 600
    }
  },
  "session": {
    "typingIntervalSeconds": 6,
    "typingTtlSeconds": 600
  }
}
```

- `typingIntervalSeconds`: typing indicator发送间隔（默认6秒）
- `typingTtlSeconds`: typing indicator超时时间（默认120秒，现已改为600秒=10分钟）

### Sandbox配置

已更新 `~/openclaw-sandbox/config/openclaw.json`，设置 `typingTtlSeconds: 600`（10分钟）。

### 注意事项

⚠️ **OpenClaw升级时会丢失修改**，需要重新应用patch或向OpenClaw提交PR。

---

## 长期方案2：飞书进度消息更新工具（已实施）

### 工具位置

- 源码：`~/openclaw-sandbox/workspace/tools/feishu-progress.js`
- Skill：`~/openclaw-sandbox/workspace/skills/feishu-progress/SKILL.md`

### 功能

不依赖typing indicator，通过消息更新API显示进度：
- 发送初始消息："⏳ 正在处理..."
- 更新进度："▓▓▓▓▓░░░░░ 50%\n正在生成文案...\n⏱️ 1分30秒"
- 完成时更新："✅ 任务完成\n⏱️ 总耗时: 2分钟"

### 使用方法

```bash
# 开始
node tools/feishu-progress.js start <chatId> "⏳ 正在处理..."

# 更新进度
node tools/feishu-progress.js update --step 1 --total 3 "🔍 正在研究..."

# 完成
node tools/feishu-progress.js complete "✅ 任务完成"

# 错误
node tools/feishu-progress.js error "❌ 处理失败"
```

### 环境变量

需要设置（已在OpenClaw配置中）：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_DOMAIN`（可选）

---

## 短期方案（已实施）

### 1. Streaming Card（已启用）
- 配置：`streaming: true` + `renderMode: "auto"`

### 2. 进度输出规则（SOUL.md）
在"运行时纪律"中添加了第4条：每20-30秒必须输出进度更新。

### 3. 长任务心跳（AGENTS.md）
在"心跳"部分添加了长任务进度输出机制。

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `~/openclaw-sandbox/config/openclaw.json` | typingTtlSeconds: 600 |
| `~/openclaw-sandbox/workspace/SOUL.md` | 进度输出规则（第4条纪律） |
| `~/openclaw-sandbox/workspace/AGENTS.md` | 长任务心跳机制 |
| `~/openclaw-sandbox/workspace/tools/feishu-progress.js` | 进度消息更新工具 |
| `~/openclaw-sandbox/workspace/skills/feishu-progress/SKILL.md` | 工具使用说明 |

---

## 验证方法

1. 发送一个需要超过2分钟的任务给sandbox agent
2. 观察飞书消息：
   - typing indicator应该持续显示（现在10分钟超时）
   - 或使用进度消息工具显示进度条
3. 确认没有出现"卡住"的假象

---

## 技术细节

### Typing Controller源码（修改后）

```javascript
// openclaw/dist/auth-profiles-DRjqKE3G.js
const configuredTypingSeconds = agentCfg?.typingIntervalSeconds ?? sessionCfg?.typingIntervalSeconds;
const configuredTypingTtlSeconds = agentCfg?.typingTtlSeconds ?? sessionCfg?.typingTtlSeconds;
const typingTtlMs = (typeof configuredTypingTtlSeconds === "number" ? configuredTypingTtlSeconds : 120) * 1e3;
const typingIntervalSeconds = typeof configuredTypingSeconds === "number" ? configuredTypingSeconds : 6;

const typing = createTypingController({
  onReplyStart: opts?.onReplyStart,
  onCleanup: opts?.onTypingCleanup,
  typingIntervalSeconds,
  typingTtlMs,
  silentToken: SILENT_REPLY_TOKEN,
  log: defaultRuntime.log
});
```

### 飞书消息更新API

```javascript
// PUT /im/v1/messages/{message_id}
{
  "msg_type": "text",
  "content": "{\"text\": \"进度内容\"}"
}
```
