---
name: Pixelle-Video v1.1 状态
description: 2026-05-05 v1.1 竖屏轮播测试完成，修正横屏bug，QC修复，待接入CosyVoice+速创
type: project
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
# Pixelle-Video v1.1 状态 (2026-05-05 02:28)

## 已完成
- 克隆 AIDC-AI/Pixelle-Video，完成全架构模块映射
- AssetBasedPipeline + carousel 模式 (script_mode="carousel")
- 横屏轮播模板 `data/templates/1920x1080/carousel_kenburns.html`
- 竖屏轮播模板 `data/templates/1080x1920/carousel_kenburns.html`
- 素材分析 fallback (无 RunningHub key 也能跑)
- **竖屏轮播测试通过**: `v1_portrait_test.mp4` (1080x1920, 32s, 1.2MB)
- **v1_test.py QC 修正**: 分辨率检验从 1920x1080 改为 1080x1920
- **v1_test.py 模板修正**: frame_template 从 1920x1080 改为 1080x1920

## ⚠️ 05-05 发现的 bug
- v1_test.py 用了横屏模板 (1920x1080) 却声称是竖屏测试
- qc_check() 硬编码检验 1920x1080，竖屏输出会被标为 FAIL
- 后 3 次 pixelle 输出全是横屏 (20260505_014321/014434/014708)，前 3 次才是竖屏

## 待改进
1. 视频时长对齐 — 下载素材长度不一，需在carousel模式下统一clip时长
2. 音频归一化 — mean -30.3dB 偏小，应 normalize 到 -16dB LUFS
3. 接入 CosyVoice TTS 替换 Edge-TTS
4. 接入速创 API 替换 AI 图片生成
5. 质检环节集成进 pipeline (目前是外部脚本)

## Why
v1 竖屏轮播确认可用。之前的"横屏测试完成"报告是错误的——QC 函数硬编码了错误的分辨率，导致横屏被标记为 PASS 而竖屏会被标记为 FAIL。

## How to apply
- 竖屏测试: `python /Users/yezhong/pixelle_project/v1_test.py` → 产出 1080x1920
- 模板: 必须用 `1080x1920/carousel_kenburns.html`
- QC: 检验分辨率 1080x1920
