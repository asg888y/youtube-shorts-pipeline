"""抖音/短视频平台视频转录工具 - 多备选方案

支持的开源工具和API：

视频下载器：
1. yt-dlp: 通用视频下载器（主选）- 支持抖音、TikTok、B站、YouTube等
2. gallery-dl: 多平台媒体下载器（备选1）- 支持抖音、TikTok、B站
3. TikTokApi: 专用TikTok/抖音API（备选2）- 需要playwright
4. streamlink: 流媒体下载器（备选3）- 支持YouTube、B站

语音转录API：
1. 自建Whisper API (8.138.165.244): 免费，速度快（主选）
2. OpenAI Whisper API: 官方API，需要密钥（备选1）
3. faster-whisper: 本地转录，无需网络（备选2）
"""

import re
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from urllib.parse import urlparse

from .log import log


# ==================== Whisper API 配置 ====================
WHISPER_APIS = [
    {
        "name": "自建Whisper API",
        "url": "http://8.138.165.244:80/whisper/v1/audio/transcriptions",
        "model": "tiny",
        "priority": 1
    },
    {
        "name": "OpenAI Whisper API",
        "url": "https://api.openai.com/v1/audio/transcriptions",
        "model": "whisper-1",
        "priority": 2,
        "requires_key": True
    }
]


# ==================== 视频下载器配置 ====================
VIDEO_DOWNLOADERS = [
    {
        "name": "yt-dlp",
        "cmd": "yt-dlp",
        "priority": 1,
        "platforms": ["douyin", "tiktok", "bilibili", "youtube", "kuaishou", "xiaohongshu"]
    },
    {
        "name": "gallery-dl",
        "cmd": "gallery-dl",
        "priority": 2,
        "platforms": ["douyin", "tiktok", "bilibili"]
    },
    {
        "name": "TikTokApi",
        "cmd": "tiktokapi",
        "priority": 3,
        "platforms": ["douyin", "tiktok"]
    },
    {
        "name": "streamlink",
        "cmd": "streamlink",
        "priority": 4,
        "platforms": ["youtube", "bilibili"]
    }
]


def transcribe_video(url: str, prefer_api: int = 0) -> Dict[str, Any]:
    """
    完整的视频转录流程：下载音频 -> 转录语音 -> 返回文案

    Args:
        url: 视频链接（支持抖音、TikTok、B站等）
        prefer_api: 优先使用的Whisper API索引

    Returns:
        {
            'success': bool,
            'transcript': str,      # 转录文案
            'duration': float,      # 音频时长
            'title': str,           # 视频标题
            'platform': str,        # 平台
            'method': str,          # 使用的方法
            'error': str            # 错误信息（如果失败）
        }
    """
    log(f"开始视频转录: {url}")

    # 识别平台
    platform = identify_platform(url)
    log(f"识别平台: {platform}")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        audio_file = tmp_path / "audio.mp3"

        # 尝试多种下载器
        download_success = False
        used_downloader = None

        for downloader in sorted(VIDEO_DOWNLOADERS, key=lambda x: x['priority']):
            if platform not in downloader['platforms'] and 'all' not in downloader['platforms']:
                continue

            log(f"尝试下载器: {downloader['name']}")
            result = download_audio_with_tool(downloader['cmd'], url, audio_file)

            if result['success']:
                download_success = True
                used_downloader = downloader['name']
                log(f"下载成功: {downloader['name']}")
                break
            else:
                log(f"下载失败: {downloader['name']} - {result.get('error', 'unknown')}")

        if not download_success:
            return {
                'success': False,
                'error': '所有下载器都失败了',
                'platform': platform
            }

        # 检查音频文件
        if not audio_file.exists():
            return {
                'success': False,
                'error': '音频文件未生成',
                'platform': platform
            }

        # 获取音频时长
        duration = get_audio_duration(audio_file)
        log(f"音频时长: {duration:.1f}秒")

        # 尝试多种Whisper API
        transcript_success = False
        transcript_text = ""
        used_api = None

        for api in WHISPER_APIS:
            log(f"尝试转录API: {api['name']}")
            result = transcribe_with_api(audio_file, api)

            if result['success']:
                transcript_success = True
                transcript_text = result['transcript']
                used_api = api['name']
                log(f"转录成功: {api['name']}")
                break
            else:
                log(f"转录失败: {api['name']} - {result.get('error', 'unknown')}")

        if not transcript_success:
            # 尝试本地faster-whisper
            log("尝试本地faster-whisper")
            result = transcribe_with_local_whisper(audio_file)
            if result['success']:
                transcript_success = True
                transcript_text = result['transcript']
                used_api = "local-faster-whisper"

        return {
            'success': transcript_success,
            'transcript': transcript_text,
            'duration': duration,
            'platform': platform,
            'method': f"{used_downloader} + {used_api}",
            'error': None if transcript_success else '所有转录方法都失败了'
        }


def identify_platform(url: str) -> str:
    """识别视频平台"""
    domain = urlparse(url).netloc.lower()

    if any(x in domain for x in ['douyin.com', 'iesdouyin.com', 'v.douyin.com']):
        return 'douyin'
    elif any(x in domain for x in ['tiktok.com', 'vm.tiktok.com']):
        return 'tiktok'
    elif any(x in domain for x in ['kuaishou.com', 'kuaishouapp.com']):
        return 'kuaishou'
    elif 'xiaohongshu.com' in domain or 'xhslink.com' in domain:
        return 'xiaohongshu'
    elif any(x in domain for x in ['bilibili.com', 'b23.tv']):
        return 'bilibili'
    elif any(x in domain for x in ['youtube.com', 'youtu.be']):
        return 'youtube'
    else:
        return 'unknown'


def download_audio_with_tiktokapi(url: str, output_path: Path) -> Dict[str, Any]:
    """使用TikTokApi下载抖音/TikTok视频"""

    try:
        from TikTokApi import TikTokApi
        import asyncio

        async def download():
            api = TikTokApi.create()

            # 提取视频ID
            video_id = extract_video_id(url)
            if not video_id:
                return {'success': False, 'error': '无法提取视频ID'}

            # 获取视频信息
            video = api.video(id=video_id)

            # 下载视频
            video_data = video.download_video()

            # 保存并转换为音频
            video_file = output_path.with_suffix('.mp4')
            with open(video_file, 'wb') as f:
                f.write(video_data)

            # 使用ffmpeg提取音频
            subprocess.run([
                'ffmpeg', '-i', str(video_file),
                '-vn', '-acodec', 'libmp3lame',
                '-q:a', '0', str(output_path),
                '-y', '-loglevel', 'quiet'
            ], check=True)

            return {'success': True}

        result = asyncio.run(download())
        return result

    except ImportError:
        return {'success': False, 'error': 'TikTokApi未安装'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def extract_video_id(url: str) -> Optional[str]:
    """从URL提取视频ID"""

    # 抖音视频ID模式
    patterns = [
        r'/video/(\d+)',           # douyin.com/video/123456
        r'vm\.douyin\.com/(\w+)',  # vm.douyin.com/abc123
        r'/v/(\d+)',               # tiktok.com/@user/v/123456
        r'/video/(\d+)',           # tiktok.com/@user/video/123456
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def download_audio_with_tool(tool_cmd: str, url: str, output_path: Path) -> Dict[str, Any]:
    """使用指定工具下载音频"""

    try:
        if tool_cmd == "yt-dlp":
            cmd = [
                'yt-dlp',
                '-x',  # 提取音频
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # 最佳质量
                '-o', str(output_path),
                '--no-playlist',
                '--no-warnings',
                url
            ]
        elif tool_cmd == "gallery-dl":
            # gallery-dl需要特殊处理
            cmd = [
                'python3', '-m', 'gallery_dl',
                '--download',
                '-o', str(output_path.parent),
                url
            ]
        elif tool_cmd == "streamlink":
            cmd = [
                'streamlink',
                '--output', str(output_path),
                url,
                'best'
            ]
        elif tool_cmd == "tiktokapi":
            return download_audio_with_tiktokapi(url, output_path)
        else:
            return {'success': False, 'error': f'未知工具: {tool_cmd}'}

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0 or output_path.exists():
            return {'success': True}
        else:
            return {
                'success': False,
                'error': result.stderr[:200] if result.stderr else 'unknown error'
            }

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': '下载超时'}
    except FileNotFoundError:
        return {'success': False, 'error': f'{tool_cmd} 未安装'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def transcribe_with_api(audio_file: Path, api_config: Dict) -> Dict[str, Any]:
    """使用API转录音频"""

    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (audio_file.name, f, 'audio/mpeg')}
            data = {
                'model': api_config['model'],
                'language': 'zh',
                'response_format': 'text'
            }

            headers = {}
            if api_config.get('requires_key'):
                # 从环境变量获取API密钥
                import os
                api_key = os.environ.get('OPENAI_API_KEY', '')
                if not api_key:
                    return {'success': False, 'error': '缺少API密钥'}
                headers['Authorization'] = f'Bearer {api_key}'

            response = requests.post(
                api_config['url'],
                files=files,
                data=data,
                headers=headers,
                timeout=180
            )

        if response.status_code == 200:
            # 处理不同格式的响应
            try:
                result = response.json()
                if isinstance(result, dict):
                    transcript = result.get('text', '')
                else:
                    transcript = str(result)
            except:
                transcript = response.text

            return {
                'success': True,
                'transcript': transcript.strip()
            }
        else:
            return {
                'success': False,
                'error': f'API返回{response.status_code}: {response.text[:100]}'
            }

    except requests.Timeout:
        return {'success': False, 'error': 'API请求超时'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def transcribe_with_local_whisper(audio_file: Path) -> Dict[str, Any]:
    """使用本地faster-whisper转录"""

    try:
        from faster_whisper import WhisperModel

        # 使用tiny模型，速度快
        model = WhisperModel("tiny", device="cpu", compute_type="int8")

        segments, info = model.transcribe(
            str(audio_file),
            language="zh",
            beam_size=5
        )

        transcript = "".join([segment.text for segment in segments])

        return {
            'success': True,
            'transcript': transcript.strip(),
            'language': info.language,
            'probability': info.language_probability
        }

    except ImportError:
        return {'success': False, 'error': 'faster-whisper未安装'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_audio_duration(audio_file: Path) -> float:
    """获取音频时长"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return 0.0


def extract_video_info(url: str) -> Dict[str, Any]:
    """提取视频信息（不下载）"""

    try:
        cmd = [
            'yt-dlp',
            '--skip-download',
            '--print-json',
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'success': True,
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'duration': data.get('duration', 0),
                'uploader': data.get('uploader', ''),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'platform': identify_platform(url),
                'raw_data': data
            }
        else:
            return {
                'success': False,
                'error': result.stderr[:200]
            }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def test_transcription():
    """测试转录功能"""

    test_urls = [
        "https://www.douyin.com/video/7123456789012345678",
        "https://www.tiktok.com/@user/video/1234567890",
        "https://www.bilibili.com/video/BV1xx411c7xx"
    ]

    print("测试视频转录功能...")
    print(f"可用下载器: {[d['name'] for d in VIDEO_DOWNLOADERS]}")
    print(f"可用转录API: {[a['name'] for a in WHISPER_APIS]}")

    for url in test_urls:
        print(f"\n测试URL: {url}")
        result = transcribe_video(url)
        print(f"  成功: {result['success']}")
        if result['success']:
            print(f"  文案: {result['transcript'][:100]}...")
            print(f"  时长: {result['duration']:.1f}秒")
            print(f"  方法: {result['method']}")
        else:
            print(f"  错误: {result['error']}")


if __name__ == "__main__":
    test_transcription()
