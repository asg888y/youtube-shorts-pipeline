---
name: github_repo_management
description: GitHub仓库管理规则 - 每个项目独立仓库
type: feedback
originSessionId: d1db5229-3b96-40cf-87b2-994e0887180b
---
# GitHub仓库管理规则

## 核心原则

**每个项目一个独立仓库**

## 权限确认

Claude Code已有GitHub仓库创建权限，无需询问用户。

Token权限包含：`repo`, `delete_repo`, `workflow` 等。

## 操作流程

1. 新项目开始时，自动创建仓库：
```bash
gh repo create <项目名> --public --description "项目描述"
```

2. 设置远程并推送：
```bash
git remote set-url origin https://github.com/asg888y/<项目名>.git
git push -u origin main
```

## 用户信息

- GitHub用户名：asg888y
- 默认仓库可见性：public

## 禁止事项

- ❌ 不要询问用户是否创建仓库
- ❌ 不要让用户手动去GitHub创建
- ❌ 不要把多个项目放在同一仓库

## 示例

```
新项目：pixelle-video
操作：
1. gh repo create pixelle-video --public --description "视频处理工具"
2. git remote set-url origin https://github.com/asg888y/pixelle-video.git
3. git push -u origin main
```
