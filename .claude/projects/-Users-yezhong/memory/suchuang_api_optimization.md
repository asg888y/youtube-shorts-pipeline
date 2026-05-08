---
name: suchuang api optimization
description: Suchuang NanoBanana2 API speed optimization: 1K is 2x faster than 2K, prompt complexity irrelevant
type: reference
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
## Suchuang NanoBanana2 API 优化发现

### 速度对比（实测 2026-05-04）

| 配置 | 耗时 | 备注 |
|------|------|------|
| 1K + 简单提示词 | ~71s | 简单提示词不快 |
| 1K + 复杂提示词 | ~48s | **最快组合** |
| 2K + 简单提示词 | ~114s | 最慢 |
| 2K + 复杂提示词 | ~90s | 当前默认（已改） |

### 关键结论
- **1K 比 2K 快约 2 倍**（48s vs 90s）
- **提示词复杂度不影响速度**（复杂提示词甚至更快）
- **api.wuyinkeji.com 比文档声称的 3-5s 慢很多**，这是提供商限制
- 只有 NanoBanana2 端点可用，Pro/Gemini Flash 返回 404
- v1 端点（Bearer auth）返回 404，只能用 async 端点

### 已应用优化
- `lib/config.py`: IMAGE_SIZE 从 "2K" 改为 "1K"

### 来源
- `~/Downloads/速创使用建议.docx` — 用户提供的第三方使用经验文档
- 4 组对比测试验证
