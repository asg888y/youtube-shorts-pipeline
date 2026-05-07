"""Multi-platform upload — YouTube, Douyin, Kuaishou, Xiaohongshu, Weixin.

Supports:
- YouTube: OAuth API upload (private by default)
- Douyin: 抖音创作者平台 (草稿/仅保存)
- Kuaishou: 快手开放平台
- Xiaohongshu: 小红书创作者平台
- Weixin: 视频号 (微信)
"""

from pathlib import Path
from .log import log
from .retry import with_retry


# 平台配置
PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "api_type": "oauth",
        "draft_mode": "private",  # privacyStatus: private
    },
    "douyin": {
        "name": "抖音",
        "api_type": "openapi",
        "draft_mode": "draft",  # 仅保存不发布
    },
    "kuaishou": {
        "name": "快手",
        "api_type": "openapi",
        "draft_mode": "draft",
    },
    "xiaohongshu": {
        "name": "小红书",
        "api_type": "openapi",
        "draft_mode": "draft",
    },
    "weixin": {
        "name": "视频号",
        "api_type": "openapi",
        "draft_mode": "draft",
    },
}


@with_retry(max_retries=2, base_delay=5.0)
def upload_to_youtube(
    video_path: Path,
    draft: dict,
    srt_path: Path = None,
    lang: str = "en",
    thumbnail_path: Path = None,
    draft_only: bool = True,  # 默认仅保存不发布
) -> str:
    """Upload video to YouTube with metadata, captions, and optional thumbnail."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from .config import get_youtube_token_path, write_secret_file

    token_path = get_youtube_token_path()
    creds = Credentials.from_authorized_user_file(str(token_path))
    if creds.expired:
        if creds.refresh_token:
            creds.refresh(Request())
            write_secret_file(token_path, creds.to_json())
        else:
            raise RuntimeError(
                "YouTube OAuth token is expired and has no refresh token.\n"
                "Re-run: python3 scripts/setup_youtube_oauth.py"
            )

    youtube = build("youtube", "v3", credentials=creds)
    log(f"Uploading {video_path.name} to YouTube...")

    # draft_only=True 时设为private，不公开发布
    privacy = "private" if draft_only else "public"

    body = {
        "snippet": {
            "title": draft.get("youtube_title", draft["news"])[:100],
            "description": draft.get("youtube_description", ""),
            "tags": draft.get("youtube_tags", "").split(","),
            "categoryId": "20",
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            log(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    log(f"Uploaded: {url} (privacy: {privacy})")

    # Upload SRT if available
    if srt_path and srt_path.exists():
        try:
            youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": lang,
                        "name": lang.upper(),
                        "isDraft": False,
                    }
                },
                media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream"),
            ).execute()
            log("Captions uploaded.")
        except Exception as e:
            log(f"Caption upload failed: {e}")

    # Upload thumbnail if available
    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            log("Thumbnail uploaded.")
        except Exception as e:
            log(f"Thumbnail upload failed: {e}")

    return url


def upload_to_platform(
    platform: str,
    video_path: Path,
    draft: dict,
    draft_only: bool = True,
) -> str:
    """Upload video to specified platform.

    Args:
        platform: youtube, douyin, kuaishou, xiaohongshu, weixin
        video_path: Path to video file
        draft: Draft dict with metadata
        draft_only: True = 仅保存不发布, False = 直接发布

    Returns:
        URL or video ID
    """
    platform = platform.lower()
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform}. Supported: {list(PLATFORMS.keys())}")

    config = PLATFORMS[platform]

    if platform == "youtube":
        return upload_to_youtube(video_path, draft, draft_only=draft_only)

    # 国内平台需要API配置
    log(f"Uploading to {config['name']}...")

    # TODO: 实现各平台API
    # 抖音: 需要client_id/client_secret, OAuth授权
    # 快手: 需要app_id/app_secret
    # 小红书: 需要创作者平台API
    # 视频号: 需要微信开放平台

    raise NotImplementedError(
        f"{config['name']} upload not yet implemented.\n"
        f"需要配置 {config['name']} 开放平台API密钥。\n"
        f"当前仅支持YouTube上传。"
    )


def list_platforms() -> list[str]:
    """List all supported upload platforms."""
    return list(PLATFORMS.keys())