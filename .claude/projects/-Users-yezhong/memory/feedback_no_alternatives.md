---
name: no alternatives without approval
description: 禁止未经文字审批擅自替换方案
type: feedback
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
## 铁律

**用户提出的要求，必须100%严格按照要求执行。未经文字审批，禁止任何替代方案。**

## 典型违规

- 用户要求 Umi-OCR Rapid版 → 擅自换成 Tesseract
- 用户要求 faster-whisper int8 → 遭遇下载失败后擅自换方案
- 遇到阻碍时自作主张换方案，而不是停下报告

## 正确做法

1. 严格按用户指定的技术栈执行
2. 遇到阻碍 → 报告问题 + 提出方案A/B供选择，等待文字确认
3. 未获文字审批前，不得替换

## Why

用户指定技术栈有其原因（性能、精度、兼容性）。擅自替换 = 产出不符合要求的废品。
