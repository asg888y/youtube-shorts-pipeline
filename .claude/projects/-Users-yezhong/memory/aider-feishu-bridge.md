---
name: aider-feishu-bridge
description: 飞书-Aider 桥接服务配置经验 - 2026-05-08
type: project
originSessionId: e71362bd-5fb5-4884-a351-6e768854f71b
---
## 项目概述

通过飞书长连接远程控制 Aider 执行代码编写和短视频生产任务。

## 关键配置文件

| 文件 | 路径 | 用途 |
|------|------|------|
| 桥接脚本 | `~/feishu-aider.py` | 飞书长连接 + 命令识别 |
| Aider 配置 | `~/.aider.conf.yml` | 全局模型和行为配置 |
| 工作区 | `~/aider-workspace/` | Aider 工作目录 |
| Launchd | `~/Library/LaunchAgents/com.feishu-aider.bridge.plist` | 24小时常驻服务 |

## 飞书凭证

- App ID: `cli_a97762487cb81bc1`
- App Secret: `hasqDYNqRRz7mVcnA5YoKeIOQzaSccqU`
- 订阅方式: 长连接模式
- 事件: `im.message.receive_v1`

## 讯飞 API (OpenAI 兼容)

- API Key: `2aa8bd2de6d5184d3b373d658f3f3177:YWU0ZTVjNTg1NTM1Nzc5YzZjZDM4NTI2`
- Base URL: `https://maas-coding-api.cn-huabei-1.xf-yun.com/v2`
- 模型: `astron-code-latest`

## 中文输出配置 (重要!)

Aider 默认输出英文，需要修改源码中的提示词文件：

```bash
# 修改以下文件中的 main_system 和 system_reminder
/Users/yezhong/Library/Python/3.10/lib/python/site-packages/aider/coders/wholefile_prompts.py
/Users/yezhong/Library/Python/3.10/lib/python/site-packages/aider/coders/editblock_prompts.py
```

将 `main_system = """Act as an expert software developer...` 改为中文版本。

## 常用命令

```bash
# 查看服务状态
launchctl list | grep feishu-aider

# 查看日志
tail -f ~/feishu-aider.log

# 重启服务
launchctl kickstart gui/$(id -u)/com.feishu-aider.bridge

# CLI 模式
~/bin/aider-cli
```

## 热点视频命令

飞书发送：
- "热点视频" - 激活管线
- "1" - 获取今日热点
- "2" - 创作文案
- "3" - 生成视频
- "4" - 全自动生产

## 遇到的问题

1. **英文输出**: 需修改 aider 源码提示词
2. **Python 路径**: 使用 `/usr/local/bin/python3.10`
3. **SSL 证书**: 设置 `SSL_CERT_FILE` 环境变量
4. **配置语法**: `yes:` 改为 `yes-always:`
5. **App 冲突**: 新建飞书 App 避免与其他机器人冲突

## Why

用户希望通过飞书远程控制 Aider 进行文案创作和短视频生产，实现 24 小时常驻服务。
