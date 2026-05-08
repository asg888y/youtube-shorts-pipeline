---
name: feishu-bridge-status
description: 飞书桥接配置状态 - 2026-05-08
type: project
originSessionId: 135c089e-b375-417c-a470-25943d018d79
---
## 飞书桥接配置完成

**配置文件：** `~/.claude-to-im/config.env`

**凭证：**
- App ID: `cli_a97ed178c9b89cc7`
- App Secret: `rZEdD1CeXCsHTxsFShjAQdI4IkPmeBnA`
- 域: `https://open.feishu.cn`

**审批机制：** 已启用（非自动批准）

**Skill 路径：**
- 飞书桥接：`~/.claude/skills/feishu-bridge/`
- 核心库：`~/.claude/skills/Claude-to-IM/`

**Launchd 服务：**
- 飞书：`com.feishu-bridge.claude` ✅ 运行中
- 微信：`com.wechat-claude-code.bridge` ⏸️ 已停止（保留配置）

## 待办事项

1. **测试飞书审批流程** - 从飞书发消息触发权限请求，验证审批通知和响应
2. **微信限流问题** - 微信 ilinkai API 返回 `ret:-2` 限流，需等待解除或减少消息频率

## 常用命令

```bash
# 飞书桥接
launchctl list | grep feishu-bridge                    # 查看状态
launchctl kickstart gui/$(id -u)/com.feishu-bridge.claude  # 重启
tail -f ~/.claude-to-im/logs/bridge.log                # 查看日志

# 微信桥接
cd ~/.claude/skills/wechat-claude-code && npm run daemon -- start   # 启动
cd ~/.claude/skills/wechat-claude-code && npm run daemon -- stop    # 停止
tail -f ~/.wechat-claude-code/logs/bridge-2026-05-07.log            # 查看日志
```
