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
        "name": "本地faster-whisper",
        "url": "local",
        "model": "tiny",
        "priority": 1
    },
    {
        "name": "自建Whisper API",
        "url": "http://8.138.165.244:80/whisper/v1/audio/transcriptions",
        "model": "tiny",
        "priority": 2
    },
    {
        "name": "OpenAI Whisper API",
        "url": "https://api.openai.com/v1/audio/transcriptions",
        "model": "whisper-1",
        "priority": 3,
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
        "name": "playwright",
        "cmd": "playwright_download",
        "priority": 2,
        "platforms": ["douyin", "tiktok"]
    },
    {
        "name": "douyin-direct",
        "cmd": "douyin_direct",
        "priority": 3,
        "platforms": ["douyin"]
    },
    {
        "name": "gallery-dl",
        "cmd": "gallery-dl",
        "priority": 4,
        "platforms": ["douyin", "tiktok", "bilibili"]
    },
    {
        "name": "TikTokApi",
        "cmd": "tiktokapi",
        "priority": 5,
        "platforms": ["douyin", "tiktok"]
    },
    {
        "name": "streamlink",
        "cmd": "streamlink",
        "priority": 6,
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
            # 新版本TikTokApi用法
            api = TikTokApi()

            # 提取视频ID
            video_id = extract_video_id(url)
            if not video_id:
                return {'success': False, 'error': '无法提取视频ID'}

            async with api:
                # 获取视频信息
                video = api.video(id=video_id)

                # 获取视频数据
                video_info = await video.info()

                # 获取下载链接
                play_url = video_info.get('video', {}).get('play_addr', '')
                if not play_url:
                    # 尝试其他字段
                    play_url = video_info.get('video', {}).get('download_addr', '')

                if not play_url:
                    return {'success': False, 'error': '无法获取视频下载链接'}

                # 下载视频
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(play_url, follow_redirects=True)
                    video_file = output_path.with_suffix('.mp4')
                    with open(video_file, 'wb') as f:
                        f.write(response.content)

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

    except ImportError as e:
        return {'success': False, 'error': f'TikTokApi未安装或依赖缺失: {e}'}
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
                '--cookies-from-browser', 'chrome',  # 使用Chrome cookies
                url
            ]
        elif tool_cmd == "playwright_download":
            return download_with_playwright(url, output_path)
        elif tool_cmd == "douyin_direct":
            # 直接下载抖音视频
            return download_douyin_direct(url, output_path)
        elif tool_cmd == "gallery-dl":
            # gallery-dl 下载视频
            video_file = output_path.with_suffix('.mp4')
            cmd = [
                'python3', '-m', 'gallery_dl',
                '-o', f'base-directory={str(output_path.parent)}',
                '-o', f'filename={output_path.stem}.mp4',
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

        # gallery-dl 下载后需要转换
        if tool_cmd == "gallery-dl" and output_path.with_suffix('.mp4').exists():
            subprocess.run([
                'ffmpeg', '-i', str(output_path.with_suffix('.mp4')),
                '-vn', '-acodec', 'libmp3lame',
                '-q:a', '0', str(output_path),
                '-y', '-loglevel', 'quiet'
            ], check=True)

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


def download_with_playwright(url: str, output_path: Path) -> Dict[str, Any]:
    """使用Playwright模拟浏览器下载视频"""

    try:
        from playwright.sync_api import sync_playwright
        import time

        log(f"  使用Playwright下载...")

        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
            )
            page = context.new_page()

            # 监听网络请求，捕获视频URL
            video_urls = []

            def handle_response(response):
                url_str = response.url
                content_type = response.headers.get('content-type', '')
                # 捕获视频和音频请求
                if 'video' in content_type or '.mp4' in url_str or 'v26-web.douyinvod.com' in url_str:
                    video_urls.append(url_str)
                    log(f"    捕获: {url_str[:60]}...")

            page.on('response', handle_response)

            # 访问页面
            log(f"  加载页面...")
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
            except Exception as e:
                log(f"  页面加载警告: {e}")

            # 等待视频元素
            time.sleep(5)

            # 尝试获取视频元素
            try:
                video_element = page.query_selector('video')
                if video_element:
                    src = video_element.get_attribute('src')
                    if src:
                        # 补全相对URL
                        if src.startswith('/'):
                            src = 'https://www.iesdouyin.com' + src
                        video_urls.append(src)
                        log(f"    从video元素获取: {src[:60]}...")
            except:
                pass

            # 滚动页面触发加载
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)

            browser.close()

        if not video_urls:
            return {'success': False, 'error': '未捕获到视频URL'}

        # 下载视频（使用最后一个URL，通常是最高质量）
        video_url = video_urls[-1]
        log(f"  下载视频: {video_url[:80]}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15',
            'Referer': 'https://www.douyin.com/'
        }
        response = requests.get(video_url, headers=headers, timeout=60)
        if response.status_code != 200:
            return {'success': False, 'error': f'视频下载失败: {response.status_code}'}

        # 保存并提取音频
        video_file = output_path.with_suffix('.mp4')
        with open(video_file, 'wb') as f:
            f.write(response.content)

        subprocess.run([
            'ffmpeg', '-i', str(video_file),
            '-vn', '-acodec', 'libmp3lame',
            '-q:a', '0', str(output_path),
            '-y', '-loglevel', 'quiet'
        ], check=True)

        return {'success': True}

    except ImportError:
        return {'success': False, 'error': 'playwright未安装'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def download_douyin_direct(url: str, output_path: Path) -> Dict[str, Any]:
    """直接下载抖音视频（使用requests）"""

    try:
        # 1. 解析短链接获取视频ID
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        }

        # 跟随重定向获取真实URL
        log(f"  解析短链接...")
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        real_url = response.url
        log(f"  真实URL: {real_url}")

        # 提取视频ID
        video_id = extract_video_id(real_url)
        if not video_id:
            # 尝试从URL路径提取
            match = re.search(r'/video/(\d+)', real_url)
            if match:
                video_id = match.group(1)

        if not video_id:
            # 尝试从短链接响应中提取
            match = re.search(r'aweme_id=(\d+)', response.text)
            if match:
                video_id = match.group(1)

        if not video_id:
            return {'success': False, 'error': '无法提取视频ID'}

        log(f"  视频ID: {video_id}")

        # 2. 获取视频信息API
        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
        api_response = requests.get(api_url, headers=headers, timeout=10)

        if api_response.status_code != 200:
            return {'success': False, 'error': f'API请求失败: {api_response.status_code}'}

        data = api_response.json()

        # 3. 提取视频下载链接
        if data.get('status_code') != 0:
            # API可能需要登录，尝试备用方法
            log(f"  API返回错误，尝试备用方法...")
            return download_douyin_with_yt_dlp_video_id(video_id, output_path)

        item_list = data.get('item_list', [])
        if not item_list:
            return {'success': False, 'error': '未找到视频信息'}

        video_info = item_list[0]
        video_url = video_info.get('video', {}).get('play_addr', {}).get('url_list', [])

        if not video_url:
            # 尝试其他字段
            video_url = video_info.get('video', {}).get('download_addr', {}).get('url_list', [])

        if not video_url:
            return {'success': False, 'error': '未找到视频下载链接'}

        # 4. 下载视频
        video_download_url = video_url[0].replace('playwm', 'play')  # 无水印版本
        video_response = requests.get(video_download_url, headers=headers, timeout=30)

        if video_response.status_code != 200:
            return {'success': False, 'error': f'视频下载失败: {video_response.status_code}'}

        # 5. 保存视频并提取音频
        video_file = output_path.with_suffix('.mp4')
        with open(video_file, 'wb') as f:
            f.write(video_response.content)

        # 使用ffmpeg提取音频
        subprocess.run([
            'ffmpeg', '-i', str(video_file),
            '-vn', '-acodec', 'libmp3lame',
            '-q:a', '0', str(output_path),
            '-y', '-loglevel', 'quiet'
        ], check=True)

        return {'success': True}

    except requests.Timeout:
        return {'success': False, 'error': '请求超时'}
    except requests.RequestException as e:
        return {'success': False, 'error': f'网络错误: {e}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def download_douyin_with_yt_dlp_video_id(video_id: str, output_path: Path) -> Dict[str, Any]:
    """使用视频ID通过yt-dlp下载抖音视频"""

    try:
        # 构造完整URL
        url = f"https://www.douyin.com/video/{video_id}"

        cmd = [
            'yt-dlp',
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '-o', str(output_path),
            '--no-playlist',
            '--no-warnings',
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0 or output_path.exists():
            return {'success': True}
        else:
            return {'success': False, 'error': result.stderr[:200] if result.stderr else 'unknown'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def transcribe_with_api(audio_file: Path, api_config: Dict) -> Dict[str, Any]:
    """使用API转录音频"""

    try:
        # 检查是否是本地转录
        if api_config.get('url') == 'local':
            return transcribe_with_local_whisper(audio_file)

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
    """使用本地whisper转录（优先使用openai-whisper，回退到faster-whisper）"""

    # 首先尝试openai-whisper（已有本地模型）
    try:
        import whisper

        log("  使用openai-whisper转录...")
        model = whisper.load_model("tiny")

        result = model.transcribe(str(audio_file), language="zh")
        transcript = result.get("text", "").strip()

        return {
            'success': True,
            'transcript': transcript,
            'language': 'zh'
        }

    except ImportError:
        log("  openai-whisper未安装，尝试faster-whisper...")
    except Exception as e:
        log(f"  openai-whisper失败: {e}，尝试faster-whisper...")

    # 回退到faster-whisper
    try:
        from faster_whisper import WhisperModel

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
        return {'success': False, 'error': 'whisper和faster-whisper都未安装'}
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
