---
name: dependencies_check_required
description: 修改项目前必须读取DEPENDENCIES.md确认影响范围
type: feedback
originSessionId: d1db5229-3b96-40cf-87b2-994e0887180b
---
# 修改前强制检查

## 规则

**修改任何项目文件前，必须先读取该项目的 `DEPENDENCIES.md` 文件**

## 项目依赖文件位置

| 项目 | DEPENDENCIES.md |
|------|-----------------|
| youtube-shorts-pipeline | `/Users/yezhong/youtube-shorts-pipeline/DEPENDENCIES.md` |
| video-studio | `/Users/yezhong/video-studio/DEPENDENCIES.md` |
| video-use-new | `/Users/yezhong/video-use-new/DEPENDENCIES.md` |

## 为什么

- 避免一次修改导致全链路崩溃
- 确认调用方是否需要同步更新
- 了解外部依赖关系

## 执行流程

1. 用户请求修改某项目
2. **先读取** 该项目的 `DEPENDENCIES.md`
3. 确认影响范围
4. 执行修改
5. 同步更新调用方配置（如有）
6. 更新 `DEPENDENCIES.md` 的修改记录
