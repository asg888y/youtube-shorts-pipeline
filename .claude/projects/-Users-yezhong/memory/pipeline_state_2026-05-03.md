---
name: Pipeline state 2026-05-03
description: Video production pipeline current state — what's fixed, what's pending
type: project
originSessionId: a670e9d4-77f5-4531-b398-566d18a02f30
---
Pipeline tested on project `2026-05-03_collapse_solitude` (scripts 2 & 10, 116s video).

**Fixed:**
- TTS: `synthesizer.call(text)` — no more instruct prefix spoken aloud (`lib/tts_client.py:40`)
- Landscape videos: orientation check on ALL videos (existing + downloaded) in `lib/asset_library.py:212-227` and `lib/asset_library.py:245-260`
- Subtitle timing: even duration distribution per chunk (`lib/subtitles.py:61-65`)
- Audio/video sync: `-t audio_dur` instead of `-shortest` in composite (`pipeline.py:244`)
- EDL video slot timing: video slots = 3s, image slots absorb remaining time (`lib/edl_builder.py:78-92`)
- Image API: no retry on permanent errors like 余额不足 (`lib/image_client.py:108-112`)

**Known issues:**
- Image API (nanobanana2 via Suchuang) out of credits — only 3 images available
- Free stock platforms mostly have landscape videos; portrait ones are rare
- Only 3 video sources currently: Coverr (API), Mixkit (scrape), Splitshire (scrape), Pexels (API, needs key)
- Need more video sources — task #35 pending: search+verify 10+ free video platforms

**Why:** Pipeline was rebuilt from scratch after user found 4 critical QA failures. All fixes applied and verified on final.mp4 (116.2s, G1-G6 all passed).
