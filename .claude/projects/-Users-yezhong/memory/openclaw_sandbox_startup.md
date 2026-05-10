---
name: OpenClaw Sandbox启动方式
description: sandbox必须用start-debug.sh启动，不能用sandbox-exec（macOS 26不支持port语法）
type: feedback
originSessionId: 8aa0ab7a-a118-4ca4-9394-bcc3931aaf53
---
# OpenClaw Sandbox 启动方式

## 规则

**必须用 `start-debug.sh` 启动，不能用 `start.sh`（sandbox-exec）**

## Why

macOS 26.3.1 的 sandbox-exec 不支持 `(port X)` 和 `(limit)` 语法，会导致启动失败：
```
sandbox-exec: unbound variable: port at sandbox-profile.sb, line 55
```

之前sandbox能正常运行是因为用的是 `--profile sandbox` 模式，根本没用 sandbox-exec。

## How to apply

启动sandbox：
```bash
cd ~/openclaw-sandbox && ./start-debug.sh
```

停止sandbox：
```bash
openclaw --profile sandbox gateway stop
# 或强制
kill <PID>
```

## 相关文件

| 文件 | 用途 |
|------|------|
| `start-debug.sh` | 正确的启动脚本（使用 --profile sandbox） |
| `start.sh` | 错误的启动脚本（使用 sandbox-exec，macOS 26不兼容） |
| `sandbox-profile.sb` | sandbox-exec配置（已废弃，macOS 26语法不兼容） |

## 教训

修改配置前必须确认：
1. 当前是用什么方式启动的
2. 修改后是否还能正常启动
3. 不要盲目修改不理解的配置文件
