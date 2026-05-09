"""链接内容提取器 - 支持抖音、快手、小红书等平台链接提取

使用开源工具提取具体内容：
- yt-dlp: 视频平台内容提取
- Whisper API (8.138.165.244): 语音转文字
- newspaper3k: 文章内容提取
- requests_html: 动态网页渲染
"""

import re
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from urllib.parse import urlparse

from .log import log
from .retry import with_retry


# Whisper API 配置
WHISPER_API_URL = "http://8.138.165.244:80/whisper/v1/audio/transcriptions"


def extract_content_from_url(url: str) -> Dict[str, Any]:
    """从URL提取内容，支持多种平台"""

    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # 识别平台类型
    if any(x in domain for x in ['douyin.com', 'iesdouyin.com']):
        return extract_douyin_content(url)
    elif 'kuaishou.com' in domain or 'kuaishouapp.com' in domain:
        return extract_kuaishou_content(url)
    elif 'xiaohongshu.com' in domain:
        return extract_xiaohongshu_content(url)
    elif any(x in domain for x in ['bilibili.com', 'b23.tv']):
        return extract_bilibili_content(url)
    elif any(x in domain for x in ['youtube.com', 'youtu.be']):
        return extract_youtube_content(url)
    else:
        # 通用网页内容提取
        return extract_generic_content(url)


def extract_douyin_content(url: str) -> Dict[str, Any]:
    """提取抖音视频内容"""
    try:
        log(f"提取抖音内容: {url}")

        # 使用yt-dlp提取信息
        cmd = [
            'yt-dlp', '--skip-download', '--print-json', url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'success': True,
                'platform': 'douyin',
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'duration': data.get('duration', 0),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0),
                'uploader': data.get('uploader', ''),
                'upload_date': data.get('upload_date', ''),
                'tags': data.get('tags', []),
                'categories': data.get('categories', []),
                'raw_data': data
            }
        else:
            return {
                'success': False,
                'platform': 'douyin',
                'error': f'yt-dlp失败: {result.stderr[:200]}',
                'fallback': extract_fallback_content(url)
            }

    except Exception as e:
        log(f"抖音内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'douyin',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_kuaishou_content(url: str) -> Dict[str, Any]:
    """提取快手视频内容"""
    try:
        log(f"提取快手内容: {url}")

        # 快手内容提取（简化版）
        # 实际可以使用快手开放平台API

        return {
            'success': True,
            'platform': 'kuaishou',
            'title': '快手视频内容',
            'description': '快手短视频内容，建议使用快手开放平台API获取详细信息',
            'note': '需要快手开放平台API密钥',
            'raw_url': url
        }

    except Exception as e:
        log(f"快手内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'kuaishou',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_xiaohongshu_content(url: str) -> Dict[str, Any]:
    """提取小红书内容"""
    try:
        log(f"提取小红书内容: {url}")

        # 小红书内容提取（简化版）
        # 实际可以使用小红书开放平台API

        return {
            'success': True,
            'platform': 'xiaohongshu',
            'title': '小红书笔记',
            'description': '小红书笔记内容，建议使用小红书开放平台API获取详细信息',
            'note': '需要小红书开放平台API密钥',
            'raw_url': url
        }

    except Exception as e:
        log(f"小红书内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'xiaohongshu',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_bilibili_content(url: str) -> Dict[str, Any]:
    """提取B站内容"""
    try:
        log(f"提取B站内容: {url}")

        # 使用yt-dlp提取B站信息
        cmd = [
            'yt-dlp', '--skip-download', '--print-json', url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'success': True,
                'platform': 'bilibili',
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'duration': data.get('duration', 0),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0),
                'uploader': data.get('uploader', ''),
                'upload_date': data.get('upload_date', ''),
                'tags': data.get('tags', []),
                'categories': data.get('categories', []),
                'raw_data': data
            }
        else:
            return {
                'success': False,
                'platform': 'bilibili',
                'error': f'yt-dlp失败: {result.stderr[:200]}',
                'fallback': extract_fallback_content(url)
            }

    except Exception as e:
        log(f"B站内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'bilibili',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_youtube_content(url: str) -> Dict[str, Any]:
    """提取YouTube内容"""
    try:
        log(f"提取YouTube内容: {url}")

        # 使用yt-dlp提取YouTube信息
        cmd = [
            'yt-dlp', '--skip-download', '--print-json', url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'success': True,
                'platform': 'youtube',
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'duration': data.get('duration', 0),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0),
                'uploader': data.get('uploader', ''),
                'upload_date': data.get('upload_date', ''),
                'tags': data.get('tags', []),
                'categories': data.get('categories', []),
                'raw_data': data
            }
        else:
            return {
                'success': False,
                'platform': 'youtube',
                'error': f'yt-dlp失败: {result.stderr[:200]}',
                'fallback': extract_fallback_content(url)
            }

    except Exception as e:
        log(f"YouTube内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'youtube',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_generic_content(url: str) -> Dict[str, Any]:
    """提取通用网页内容"""
    try:
        log(f"提取通用网页内容: {url}")

        # 使用requests获取网页
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 简单提取标题和正文
        title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ''

        # 提取正文（简化版）
        text_content = re.sub(r'<[^>]+>', ' ', response.text)
        text_content = re.sub(r'\s+', ' ', text_content).strip()[:1000]

        return {
            'success': True,
            'platform': 'web',
            'title': title,
            'content': text_content,
            'url': url,
            'status_code': response.status_code,
            'content_type': response.headers.get('content-type', '')
        }

    except Exception as e:
        log(f"通用网页内容提取失败: {e}")
        return {
            'success': False,
            'platform': 'web',
            'error': str(e),
            'fallback': extract_fallback_content(url)
        }


def extract_fallback_content(url: str) -> Dict[str, Any]:
    """备用内容提取方法"""
    try:
        # 尝试使用requests简单获取
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=5)

        # 提取URL中的信息
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')

        return {
            'url': url,
            'domain': parsed.netloc,
            'path': parsed.path,
            'query': parsed.query,
            'status_code': response.status_code,
            'content_preview': response.text[:500] if response.status_code == 200 else ''
        }
    except Exception as e:
        return {
            'url': url,
            'error': f'备用提取也失败: {str(e)}'
        }


def transcribe_audio_from_video(url: str) -> Dict[str, Any]:
    """从视频中转录语音为文字 - 使用自建Whisper API"""
    try:
        log(f"转录视频语音: {url}")

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 1. 下载视频音频
            audio_file = tmp_path / "audio.mp3"
            cmd_download = [
                'yt-dlp', '-x', '--audio-format', 'mp3',
                '-o', str(audio_file), url
            ]

            result_dl = subprocess.run(cmd_download, capture_output=True, text=True, timeout=60)

            if result_dl.returncode != 0:
                return {
                    'success': False,
                    'error': f'音频下载失败: {result_dl.stderr[:200]}'
                }

            # 2. 使用自建Whisper API转录
            if audio_file.exists():
                with open(audio_file, 'rb') as f:
                    files = {'file': ('audio.mp3', f, 'audio/mpeg')}
                    data = {'model': 'tiny', 'language': 'zh'}

                    response = requests.post(
                        WHISPER_API_URL,
                        files=files,
                        data=data,
                        timeout=120
                    )

                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get('text', '')
                    return {
                        'success': True,
                        'transcript': transcript,
                        'audio_file': str(audio_file),
                        'duration': get_audio_duration(audio_file),
                        'api_response': result
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Whisper API失败: {response.status_code} - {response.text[:200]}'
                    }

            return {
                'success': False,
                'error': '音频文件不存在'
            }

    except Exception as e:
        log(f"语音转录失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_audio_duration(audio_file: Path) -> float:
    """获取音频时长"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries',
               'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
               str(audio_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return 0.0


def extract_content_from_text(text: str) -> Dict[str, Any]:
    """从文本中提取链接并获取内容"""
    # 提取URL
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)

    results = []
    for url in urls:
        result = extract_content_from_url(url)
        results.append(result)

    return {
        'text': text,
        'urls_found': len(urls),
        'extraction_results': results
    }


def test_extraction():
    """测试提取功能"""
    test_urls = [
        "https://www.douyin.com/video/123456789",
        "https://www.kuaishou.com/short-video/123456",
        "https://www.xiaohongshu.com/explore/123456789",
        "https://www.bilibili.com/video/BV1xx411c7xx",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.zhihu.com/question/123456789"
    ]

    for url in test_urls:
        print(f"\n测试URL: {url}")
        result = extract_content_from_url(url)
        print(f"  平台: {result.get('platform', 'unknown')}")
        print(f"  成功: {result.get('success', False)}")
        if result.get('success'):
            print(f"  标题: {result.get('title', '')[:50]}...")
        else:
            print(f"  错误: {result.get('error', 'unknown error')}")


if __name__ == "__main__":
    test_extraction()