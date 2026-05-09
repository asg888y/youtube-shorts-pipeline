"""Background music — track selection + volume ducking + network music fetch."""

import random
from pathlib import Path

from .config import load_config
from .log import log

# Music directory ships with the package
MUSIC_DIR = Path(__file__).resolve().parent.parent / "music"

# 风格对应的音乐子目录和情绪关键词
NICHE_MUSIC_CONFIG = {
    "emotion": {"subdir": "emotion", "mood": "warm calm emotional"},
    "viral": {"subdir": "viral", "mood": "energetic intense dramatic"},
    "knowledge": {"subdir": "knowledge", "mood": "professional clear informative"},
    "horror": {"subdir": "horror", "mood": "dark suspense mysterious"},
    "tech": {"subdir": "tech", "mood": "modern electronic futuristic"},
    "general": {"subdir": "general", "mood": "ambient neutral"},
    "multi_empty_bureau": {"subdir": "tech", "mood": "tense serious"},
}

# 国内免费音乐资源
FREE_MUSIC_SOURCES = {
    # 爱给网 - 免费音效/背景音乐
    "aigei": {
        "search": "https://www.aigei.com/s?q={mood}+背景音乐&type=music",
        "direct": "https://data.aigei.com/audio/{id}.mp3",
    },
    # 耳聆网 - 免费音效
    "freesound": {
        "search": "https://www.ear0.com/sound/search?kw={mood}",
    },
}


def _get_pexels_key() -> str:
    """Get Pexels API key from config."""
    cfg = load_config()
    return cfg.get("PEXELS_API_KEY", "")


def _fetch_free_music(mood: str = "ambient") -> Path | None:
    """Fetch free background music from 国内免费资源.

    Returns path to downloaded music file, or None if failed.
    """
    import requests
    import time

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    # 方案1: 使用Pixabay音乐API (如果有key)
    pexels_key = _get_pexels_key()
    if pexels_key:
        try:
            # Pixabay音乐搜索
            url = "https://pixabay.com/api/"
            params = {
                "key": pexels_key,
                "q": f"{mood} background music",
                "per_page": 5,
                "category": "music",
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                hits = data.get("hits", [])
                if hits:
                    # 下载第一个结果
                    audio_url = hits[0].get("pageURL")
                    if audio_url:
                        out_path = MUSIC_DIR / f"network_{int(time.time())}.mp3"
                        resp = requests.get(audio_url, timeout=60)
                        if len(resp.content) > 10000:
                            out_path.write_bytes(resp.content)
                            log(f"Downloaded network music: {out_path.name}")
                            return out_path
        except Exception as e:
            log(f"Pexels music fetch failed: {e}")

    # 方案2: 使用预设的免费音乐URL列表 (无需API key)
    # 这些是公开的免费背景音乐资源
    free_music_urls = [
        # Pixabay免费音乐 (公开可访问)
        "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",  # Ambient
        "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946bc3eb81.mp3",  # Calm
        "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",  # Electronic
    ]

    for url in free_music_urls:
        try:
            out_path = MUSIC_DIR / f"free_{int(time.time())}.mp3"
            resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 50000:
                out_path.write_bytes(resp.content)
                log(f"Downloaded free music: {out_path.name}")
                return out_path
        except Exception as e:
            log(f"Free music download failed: {e}")
            continue

    log("No network music available")
    return None


def _find_tracks(niche: str = None) -> list[Path]:
    """Find all MP3 tracks in the music/ directory.

    If niche is specified, look in style-specific subdirectory first.
    Falls back to general music if niche has no tracks.
    """
    if not MUSIC_DIR.exists():
        return []

    # If niche specified, try niche-specific directory first
    if niche and niche in NICHE_MUSIC_CONFIG:
        niche_dir = MUSIC_DIR / NICHE_MUSIC_CONFIG[niche]["subdir"]
        if niche_dir.exists():
            tracks = sorted(niche_dir.glob("*.mp3"))
            if tracks:
                log(f"Using {niche} style music ({len(tracks)} tracks)")
                return tracks

    # Fall back to general music
    general_dir = MUSIC_DIR / "general"
    if general_dir.exists():
        tracks = sorted(general_dir.glob("*.mp3"))
        if tracks:
            return tracks

    # Last resort: all music in root
    return sorted(MUSIC_DIR.glob("*.mp3"))


def _get_speech_regions(audio_path: Path) -> list[tuple[float, float]]:
    """Extract speech regions from Whisper word timestamps (reuses captions data).

    Falls back to treating the entire audio as one speech region.
    """
    try:
        from .captions import _whisper_word_timestamps
        words = _whisper_word_timestamps(audio_path)
        if words:
            # Merge close words into speech regions (gap < 0.5s = same region)
            regions = []
            region_start = words[0]["start"]
            region_end = words[0]["end"]

            for w in words[1:]:
                if w["start"] - region_end < 0.5:
                    region_end = w["end"]
                else:
                    regions.append((region_start, region_end))
                    region_start = w["start"]
                    region_end = w["end"]
            regions.append((region_start, region_end))
            return regions
    except Exception:
        pass

    # Fallback: get total duration and treat as one speech region
    try:
        from .assemble import get_audio_duration
        dur = get_audio_duration(audio_path)
        return [(0.0, dur)]
    except Exception:
        return [(0.0, 60.0)]


def build_duck_filter(speech_regions: list[tuple[float, float]], buffer: float = 0.3, vol_speech: float = 0.12, vol_gap: float = 0.25) -> str:
    """Build ffmpeg volume filter expression for ducking during speech.

    During speech: volume = vol_speech (default 0.12)
    During gaps: volume = vol_gap (default 0.25)
    Transitions smoothed by ±buffer seconds.
    """
    if not speech_regions:
        return f"volume={vol_gap}"

    # Build between() conditions for speech regions
    conditions = []
    for start, end in speech_regions:
        s = max(0, start - buffer)
        e = end + buffer
        conditions.append(f"between(t,{s:.2f},{e:.2f})")

    condition_expr = "+".join(conditions)
    return f"volume='if({condition_expr}, {vol_speech}, {vol_gap})':eval=frame"


def select_and_prepare_music(
    voiceover_path: Path,
    work_dir: Path,
    duck_speech: float = 0.12,
    duck_gap: float = 0.25,
    mood: str = "ambient",
    niche: str = None,
) -> dict:
    """Select a random track, build duck filter from speech regions.

    Falls back to network music fetch if no local tracks.
    Returns dict with track_path and duck_filter for use by assemble.py.
    """
    tracks = _find_tracks(niche=niche)

    # If no local tracks, try to fetch from network
    if not tracks:
        log("No local music tracks — trying network fetch...")
        # Use niche-specific mood if available
        fetch_mood = NICHE_MUSIC_CONFIG.get(niche, {}).get("mood", mood) if niche else mood
        network_track = _fetch_free_music(fetch_mood)
        if network_track:
            tracks = [network_track]

    if not tracks:
        log("No music tracks available — skipping background music")
        return {}

    track = random.choice(tracks)
    log(f"Selected music track: {track.name}")

    # Get speech regions for ducking
    speech_regions = _get_speech_regions(voiceover_path)
    duck_filter = build_duck_filter(speech_regions, vol_speech=duck_speech, vol_gap=duck_gap)
    log(f"Built duck filter with {len(speech_regions)} speech regions")

    return {
        "track_path": str(track),
        "duck_filter": duck_filter,
    }
