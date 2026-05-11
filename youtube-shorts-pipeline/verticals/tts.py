"""Multi-provider TTS — Edge TTS (free default), ElevenLabs (premium), macOS say (fallback), DashScope (百炼).

Edge TTS is the recommended default: free, cross-platform, 300+ voices, no API key.
ElevenLabs is premium: most natural, requires API key.
DashScope (百炼) is Alibaba Cloud TTS: Chinese/English support.
macOS say is the last-resort fallback.
"""

import os
from pathlib import Path

import requests

from .config import VOICE_ID_EN, VOICE_ID_HI, get_elevenlabs_key, run_cmd, load_config
from .log import log
from .retry import with_retry

# ─────────────────────────────────────────────────────
# Edge TTS — free, cross-platform, 300+ voices
# ─────────────────────────────────────────────────────

# Default Edge TTS voices per language
EDGE_VOICES = {
    "en": "en-US-GuyNeural",
    "hi": "hi-IN-MadhurNeural",
    "es": "es-MX-JorgeNeural",
    "pt": "pt-BR-AntonioNeural",
    "de": "de-DE-ConradNeural",
    "fr": "fr-FR-HenriNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
}


async def _edge_tts_generate(text: str, voice: str, output_path: Path):
    """Generate audio via edge-tts (async)."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def _generate_edge_tts(script: str, out_dir: Path, lang: str, voice_override: str = "") -> Path:
    """Generate voiceover via Edge TTS (free Microsoft voices)."""
    import asyncio

    voice = voice_override or EDGE_VOICES.get(lang[:2], EDGE_VOICES["en"])
    out_path = out_dir / f"voiceover_{lang}.mp3"

    log(f"Generating {lang} voiceover via Edge TTS (voice: {voice})...")

    try:
        # Handle event loop — works whether called from sync or async context
        try:
            loop = asyncio.get_running_loop()
            # Already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    _edge_tts_generate(script, voice, out_path)
                )
                future.result(timeout=60)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            asyncio.run(_edge_tts_generate(script, voice, out_path))

        log(f"Edge TTS voiceover saved: {out_path.name}")
        return out_path
    except Exception as e:
        raise RuntimeError(f"Edge TTS failed: {e}")


# ─────────────────────────────────────────────────────
# ElevenLabs — premium, most natural
# ─────────────────────────────────────────────────────

@with_retry(max_retries=3, base_delay=2.0)
def _call_elevenlabs(script: str, voice_id: str, api_key: str, settings: dict | None = None) -> bytes:
    """Call ElevenLabs TTS API and return audio bytes."""
    voice_settings = settings or {
        "stability": 0.4,
        "similarity_boost": 0.85,
        "style": 0.3,
        "use_speaker_boost": True,
    }
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": voice_settings,
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    return r.content


def _generate_elevenlabs(
    script: str, out_dir: Path, lang: str,
    voice_id: str = "", settings: dict | None = None
) -> Path:
    """Generate voiceover via ElevenLabs."""
    api_key = get_elevenlabs_key()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    vid = voice_id or (VOICE_ID_HI if lang == "hi" else VOICE_ID_EN)
    out_path = out_dir / f"voiceover_{lang}.mp3"

    log(f"Generating {lang} voiceover via ElevenLabs (voice: {vid})...")
    audio_bytes = _call_elevenlabs(script, vid, api_key, settings)
    out_path.write_bytes(audio_bytes)
    log(f"ElevenLabs voiceover saved: {out_path.name}")
    return out_path


# ─────────────────────────────────────────────────────
# macOS say — last resort fallback
# ─────────────────────────────────────────────────────

def _generate_say(script: str, out_dir: Path, lang: str = "en") -> Path:
    """macOS 'say' fallback TTS."""
    out_path = out_dir / "voiceover_say.aiff"
    mp3_path = out_dir / "voiceover_say.mp3"
    # Use Alex voice for English, default for others
    voice = ["-v", "Alex"] if lang.startswith("en") else []
    run_cmd(["say"] + voice + ["-o", str(out_path), script])
    run_cmd(
        ["ffmpeg", "-i", str(out_path), "-acodec", "libmp3lame",
        str(mp3_path), "-y", "-loglevel", "quiet",
    ])
    return mp3_path


# ─────────────────────────────────────────────────────
# DashScope (百炼) TTS — Alibaba Cloud
# ─────────────────────────────────────────────────────

# 从config.py读取TTS配置
from .config import TTS_MODEL, TTS_VOICE_ID, TTS_SPEECH_RATE

# 百炼 TTS 配置 - 自定义音色 longsanshu_v3
# 模型: qwen3-tts-vd-2026-01-26
# 音色: qwen-tts-vd-bailian-voice-20260510160239061-ba05
# 语速: 1.0 (正常)
DASHSCOPE_TTS_MODEL = TTS_MODEL
DASHSCOPE_VOICE_ID = TTS_VOICE_ID
DASHSCOPE_SPEECH_RATE = TTS_SPEECH_RATE


def _get_dashscope_key() -> str:
    """Get DashScope API key from config."""
    cfg = load_config()
    return cfg.get("DASHSCOPE_API_KEY", "")


@with_retry(max_retries=3, base_delay=2.0)
def _generate_dashscope_tts(script: str, out_dir: Path, lang: str) -> Path:
    """Generate voiceover via DashScope 百炼 TTS.

    模型: qwen3-tts-vd-2026-01-26
    音色: qwen-tts-vd-bailian-voice-20260510160239061-ba05
    """
    api_key = _get_dashscope_key()
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY not set")

    import os
    import certifi
    os.environ["DASHSCOPE_API_KEY"] = api_key
    os.environ["SSL_CERT_FILE"] = certifi.where()

    from dashscope.audio.qwen_tts import SpeechSynthesizer

    out_path = out_dir / f"voiceover_{lang}.wav"

    log(f"Generating {lang} voiceover via 百炼 TTS (model: {DASHSCOPE_TTS_MODEL}, voice: {DASHSCOPE_VOICE_ID})...")

    # 使用SpeechSynthesizer.call静态方法
    response = SpeechSynthesizer.call(
        model=DASHSCOPE_TTS_MODEL,
        text=script,
        voice=DASHSCOPE_VOICE_ID,
    )

    if not response.output:
        raise RuntimeError("百炼 TTS returned empty audio")

    # 从URL下载音频
    audio_info = response.output.get('audio', {})
    audio_url = audio_info.get('url', '')
    audio_data = audio_info.get('data', '')

    if audio_url:
        import requests
        r = requests.get(audio_url)
        out_path.write_bytes(r.content)
        log(f"百炼 TTS voiceover saved: {out_path.name}")
        return out_path
    elif audio_data:
        import base64
        audio_bytes = base64.b64decode(audio_data)
        out_path.write_bytes(audio_bytes)
        log(f"百炼 TTS voiceover saved: {out_path.name}")
        return out_path
    else:
        raise RuntimeError("百炼 TTS returned empty audio data")
    return out_path


# ─────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────

def get_tts_provider(name: str | None = None) -> str:
    """Resolve which TTS provider to use.

    强制使用 DashScope (百炼) 作为唯一 TTS 提供商。
    """
    return "dashscope"


def generate_voiceover(
    script: str,
    out_dir: Path,
    lang: str = "en",
    provider: str | None = None,
    voice_config: dict | None = None,
) -> Path:
    """Generate voiceover via DashScope 百炼 TTS (唯一 TTS 提供商).

    模型: qwen3-tts-vd-2026-01-26
    音色: qwen-tts-vd-bailian-voice-20260510160239061-ba05

    Args:
        script: The voiceover text.
        out_dir: Directory to save the audio file.
        lang: Language code (en, zh, hi, etc.).
        provider: 忽略，强制使用 dashscope。
        voice_config: 忽略，强制使用自定义音色。

    Returns:
        Path to the generated audio file.
    """
    return _generate_dashscope_tts(script, out_dir, lang)