"""B-roll generation via RunningHub API + Ken Burns animation."""

import base64
import shutil
import time
from pathlib import Path

import requests
from PIL import Image

from .config import VIDEO_WIDTH, VIDEO_HEIGHT, load_config
from .log import log
from .retry import with_retry


def _get_runninghub_key() -> str:
    """Get RunningHub API key from config."""
    cfg = load_config()
    return cfg.get("RUNNINGHUB_API_KEY", "")


def _generate_image_runninghub(prompt: str, output_path: Path, api_key: str):
    """Generate image via RunningHub OpenAPI v2 (async with polling)."""
    submit_url = "https://www.runninghub.cn/openapi/v2/rhart-image-v1/text-to-image"
    poll_url = "https://www.runninghub.cn/openapi/v2/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "prompt": prompt,
        "aspectRatio": "9:16",
    }

    # Submit task
    r = requests.post(submit_url, json=body, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"RunningHub API {r.status_code}: {r.text[:300]}")

    data = r.json()
    task_id = data.get("taskId")
    if not task_id:
        raise RuntimeError(f"No taskId in response: {data}")

    log(f"  Task submitted: {task_id}")

    # Poll for result (max 150 seconds)
    for i in range(30):
        time.sleep(5)
        poll_r = requests.post(poll_url, json={"taskId": task_id}, headers=headers, timeout=10)
        poll_data = poll_r.json()
        status = poll_data.get("status")

        if status == "SUCCESS":
            results = poll_data.get("results", [])
            if results and "url" in results[0]:
                img_url = results[0]["url"]
                img_r = requests.get(img_url, timeout=30)
                output_path.write_bytes(img_r.content)
                cost = poll_data.get("usage", {}).get("thirdPartyConsumeMoney", "?")
                log(f"  Image generated ${cost} in {(i+1)*5}s")
                return
            else:
                raise RuntimeError(f"No image URL in response: {poll_data}")
        elif status == "FAIL":
            raise RuntimeError(f"RunningHub task failed: {poll_data.get('errorMessage', 'unknown')}")

    raise RuntimeError("RunningHub timeout after 150s")


def _get_standard_color_frames() -> list[Path]:
    """获取标准纯色素材库"""
    base_dir = Path(__file__).parent.parent / "standard_assets" / "images" / "colors"
    if not base_dir.exists():
        return []
    frames = sorted(base_dir.glob("color_*.png"))
    return frames


def _get_recent_generated_frames() -> list[Path]:
    """从最近生成的工作文件夹中提取素材"""
    import glob
    media_dir = Path.home() / ".verticals" / "media"
    if not media_dir.exists():
        return []

    # 查找最近的工作文件夹
    work_dirs = sorted(media_dir.glob("work_*"), key=lambda x: x.stat().st_mtime, reverse=True)

    frames = []
    for work_dir in work_dirs[:3]:  # 检查最近3个工作文件夹
        if work_dir.is_dir():
            # 查找broll图片
            broll_files = sorted(work_dir.glob("broll_*.png"))
            if broll_files:
                frames.extend(broll_files)
                log(f"  从历史工作文件夹提取素材: {work_dir.name} ({len(broll_files)}张)")

    return frames[:20]  # 最多返回20张


def _get_local_frames(theme: str = None) -> list[Path]:
    """Get local fallback frames from local_assets/images.

    Args:
        theme: Optional theme subdirectory (e.g., "military", "tech")
    """
    # 首先尝试最近生成的工作文件夹
    recent_frames = _get_recent_generated_frames()
    if recent_frames:
        return recent_frames

    # 然后尝试标准纯色素材库
    color_frames = _get_standard_color_frames()
    if color_frames:
        return color_frames

    # 最后尝试历史素材库
    base_dir = Path(__file__).parent.parent / "local_assets" / "images"

    # 如果指定主题，先尝试主题目录
    if theme:
        theme_dir = base_dir / theme
        if theme_dir.exists():
            frames = sorted(theme_dir.glob("*.png"))
            if frames:
                return frames

    # 回退到通用目录
    if not base_dir.exists():
        return []
    frames = sorted(base_dir.glob("broll_*.png"))
    if not frames:
        frames = sorted(base_dir.glob("*.png"))
    return frames


def _fallback_frame(i: int, out_dir: Path, theme: str = None) -> Path:
    """Fallback frame: recent generated first, then standard colors, then local assets, then solid colour."""
    # 首先尝试最近生成的工作文件夹
    recent_frames = _get_recent_generated_frames()
    if recent_frames:
        src = recent_frames[i % len(recent_frames)]
        dst = out_dir / f"broll_{i}.png"
        shutil.copy2(src, dst)
        log(f"  使用历史生成素材: {src.parent.name}/{src.name}")
        return dst

    # 然后尝试标准纯色素材库
    color_frames = _get_standard_color_frames()
    if color_frames:
        src = color_frames[i % len(color_frames)]
        dst = out_dir / f"broll_{i}.png"
        shutil.copy2(src, dst)
        log(f"  使用标准纯色素材: {src.name}")
        return dst

    # 然后尝试历史素材
    local_frames = _get_local_frames(theme)
    if local_frames:
        src = local_frames[i % len(local_frames)]
        dst = out_dir / f"broll_{i}.png"
        shutil.copy2(src, dst)
        log(f"  使用历史素材: {src.name}")
        return dst

    # 最后回退到纯色背景
    colors = [(20, 20, 60), (40, 10, 40), (10, 30, 50)]
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), colors[i % len(colors)])
    path = out_dir / f"broll_{i}.png"
    img.save(path)
    log(f"  生成纯色背景")
    return path


def generate_broll(prompts: list, out_dir: Path, use_local: bool = False, theme: str = None) -> list[Path]:
    """Generate b-roll frames via RunningHub API, with fallback.

    Args:
        prompts: List of prompts (max 20 will be processed)
        out_dir: Output directory for frames
        use_local: If True, use local assets only (no API calls)
        theme: Optional theme for local assets (e.g., "military", "tech")

    Returns:
        List of generated frame paths
    """
    # 上限20张
    prompts = prompts[:20]
    num_frames = len(prompts)
    frames = []

    # 如果指定使用本地素材，直接返回历史素材
    if use_local:
        log(f"使用历史素材（主题: {theme or '通用'}）...")
        for i in range(num_frames):
            frames.append(_fallback_frame(i, out_dir, theme))
        return frames

    api_key = _get_runninghub_key()
    if not api_key:
        log("No RUNNINGHUB_API_KEY found — using fallback frames")
        for i in range(num_frames):
            frames.append(_fallback_frame(i, out_dir, theme))
        return frames

    for i, prompt in enumerate(prompts):
        out_path = out_dir / f"broll_{i}.png"
        log(f"Generating b-roll frame {i+1}/{num_frames} via RunningHub...")

        try:
            _generate_image_runninghub(prompt, out_path, api_key)

            # Resize/crop to 9:16 portrait
            img = Image.open(out_path).convert("RGB")
            target_w, target_h = VIDEO_WIDTH, VIDEO_HEIGHT
            orig_w, orig_h = img.size
            scale = max(target_w / orig_w, target_h / orig_h)
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))
            img.save(out_path)
            frames.append(out_path)

        except Exception as e:
            log(f"Frame {i+1} failed: {e} — using fallback")
            frames.append(_fallback_frame(i, out_dir, theme))

    return frames


def get_available_themes() -> list[str]:
    """获取可用的素材主题列表"""
    base_dir = Path(__file__).parent.parent / "local_assets" / "images"
    if not base_dir.exists():
        return []

    themes = []
    for d in base_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            themes.append(d.name)

    # 如果根目录有图片，添加"通用"
    if list(base_dir.glob("*.png")):
        themes.append("通用")

    return themes


def animate_frame(img_path: Path, out_path: Path, duration: float, effect: str = "zoom_in"):
    """Ken Burns animation on a single frame."""
    import subprocess
    fps = 30
    frames = int(duration * fps)
    w, h = VIDEO_WIDTH, VIDEO_HEIGHT

    if effect == "zoom_in":
        vf = (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.12-0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif effect == "pan_right":
        vf = (
            f"scale={int(w * 1.15)}:{int(h * 1.15)},"
            f"zoompan=z=1.15:x='0.15*iw*on/{frames}':y='ih*0.075'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    else:  # zoom_out
        vf = (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.0+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )

    subprocess.run([
        "ffmpeg", "-loop", "1", "-i", str(img_path),
        "-vf", vf, "-t", str(duration), "-r", str(fps),
        "-pix_fmt", "yuv420p", str(out_path), "-y", "-loglevel", "quiet",
    ], check=True)