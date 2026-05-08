---
name: User preferences for video pipeline
description: How the user wants the video pipeline to work
type: user
originSessionId: a670e9d4-77f5-4531-b398-566d18a02f30
---
User is building automated Chinese viral short-video pipeline (视频号/抖音).

**Non-negotiable:**
- NO auth prompts during pipeline execution — fully automated
- TTS: CosyVoice-v3-plus + longanyang ONLY, via DashScope
- Images: nanobanana2 ONLY, via Suchuang API
- Video sources: free, no-auth, China-accessible platforms
- Quality: never compromise — if素材isn't right, don't use it
- Landscape videos: REJECT (9:16 vertical pipeline only)

**User communication style:**
- Direct, practical, hates over-engineering
- Wants concise answers, not essays
- Test before claiming success
- Open the output directory after generating files so they don't have to search
- Permission prompt sounds matter — they don't always watch the screen

**Why:** User previously got very angry about quality failures that were "obvious" (TTS reading instruct text, landscape videos in portrait pipeline, subtitles not timed, audio cut off). They value working solutions over elaborate architecture.
