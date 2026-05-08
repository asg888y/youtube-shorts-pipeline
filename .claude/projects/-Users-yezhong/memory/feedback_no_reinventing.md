---
name: permanent ban on reinventing wheels
description: 永久禁令：做任何工具/功能前，必须先搜索50+网络资源，确认无现成方案后才能自己造
type: feedback
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---

## 永久禁令

**禁止反复发明轮子。**

## 规则

做任何工具、功能、脚本之前：

1. **先搜索 50 个以上网络资源**（GitHub、Google、HuggingFace、ProductHunt、Reddit、知乎等）
2. **确认三个问题**：
   - 有没有人已经解决了这个问题？
   - 有没有非常省事的开源免费工具？
   - 有没有现成的 SaaS/API 可以调用？
3. **只有三个答案都是"没有"，才能自己写代码**
4. **能用现有工具组合的，绝不写新代码**

## Why

- pixelle 管线调通后被 video_creator/pipeline.py 重写 → 大量调试时间白费
- OCR 客户端、TTS 客户端、图片客户端、字幕、混音全部从零写 → 每个模块都有现成开源方案
- 反复发明轮子 = 浪费用户时间、API 额度、服务器资源、token

## 执行

- 收到任何工具/功能需求 → 先搜索 → 列出已有方案 → 用户确认后才动手
- CLI 输出搜索过程和结果，让用户看到确实搜了 50+
