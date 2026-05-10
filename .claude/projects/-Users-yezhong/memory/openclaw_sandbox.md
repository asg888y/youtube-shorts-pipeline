---
name: OpenClaw Sandbox 部署
description: 独立OpenClaw沙箱环境配置、常用命令、维护要点
type: project
originSessionId: 1fca5ddc-68a5-4918-ab92-f130e8b524ed
---
# OpenClaw Sandbox 独立部署

## 基本信息

| 项目 | 值 |
|------|-----|
| Profile | `sandbox` |
| 配置目录 | `~/.openclaw-sandbox/` |
| 工作空间 | `~/openclaw-sandbox/workspace/` |
| Gateway端口 | `18790` |
| 日志文件 | `/tmp/openclaw-sandbox.log` |
| GitHub | https://github.com/asg888y/openclaw-sandbox |

## 当前模型配置

- **主模型**: `minimax/MiniMax-M2.7`
- **备用模型**: `xunfei/astron-code-latest`

## 飞书配置

- App ID: `cli_a97762487cb81bc1`
- 模式: 公开模式 (dmPolicy: open)
- 连接方式: WebSocket 长连接

## 常用命令

```bash
# 启动（前台）
openclaw --profile sandbox gateway --port 18790

# 启动（后台）
nohup openclaw --profile sandbox gateway --port 18790 > /tmp/openclaw-sandbox.log 2>&1 &

# 停止
pkill -f "openclaw --profile sandbox"

# 检查状态
pgrep -f "openclaw --profile sandbox" && echo "运行中" || echo "已停止"

# 检查端口
lsof -i :18790

# 查看日志
tail -f /tmp/openclaw-sandbox.log

# 编辑配置
nano ~/.openclaw-sandbox/openclaw.json
```

## 切换模型

编辑 `~/.openclaw-sandbox/openclaw.json`，修改两处：
1. `agents.defaults.model.primary`
2. `channels.feishu.model`

可用模型：
- `minimax/MiniMax-M2.7` - MiniMax (当前默认)
- `xunfei/astron-code-latest` - 讯飞星火代码

## 维护要点

1. **端口冲突**: 如遇 "gateway already running"，先清理端口：
   ```bash
   lsof -ti :18790 | xargs kill -9
   ```

2. **配置生效**: 修改配置后需重启服务

3. **飞书长连接**: 确保飞书开放平台已开启长连接模式

4. **后台运行**: 使用 nohup 后台启动，关闭终端不影响服务

## Why: 独立于主OpenClaw(~/.openclaw)，使用讯飞/MiniMax模型，飞书公开模式
## How to apply: 用户提到"沙箱openclaw"或需要独立部署时引用此记忆
