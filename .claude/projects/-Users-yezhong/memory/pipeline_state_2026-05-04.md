---
name: Pipeline state 2026-05-04
description: Video production pipeline current state — bugs fixed, tested, known issues
type: project
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
Pipeline tested on two projects:
- `2026-05-03_collapse_solitude` (scripts 2 & 10, 116.2s)
- `2026-05-04_loneliness` (script 1, 40.6s, longanhuan + sad + speed 1.0)

**Fixed 2026-05-04:**
- OCR: dimension limit 3000px + retry logic (`lib/ocr_client.py`, `lib/config.py:60`)
- TTS: `_detect_emotion` no longer returns "neutral" — mapped to "fearful" (`lib/selector.py:129`)
- TTS: `batch_generate` forwards voice/speed/pitch/volume from scripts (`lib/tts_client.py:98`)
- QA: G3 BGM gate now enforced — was checked but not blocking (`pipeline.py:218`)
- Config: `validate_config()` at pipeline startup checks API keys, model names (`lib/config.py`)
- Pipeline: emotion sanitization on load to catch old selection.json with "neutral" (`pipeline.py:332`)

**Known issues:**
- Image API (nanobanana2 via Suchuang) out of credits — pipeline degrades gracefully
- Free stock platforms mostly have landscape videos; need more portrait sources (task #35)
- Only 3 video sources: Coverr, Mixkit, Splitshire, Pexels (needs key)

**Why:** User triggered "bbb" — forced me to audit and fix remaining pipeline bugs after OCR client work. Verification tests passed on both old and new projects.
