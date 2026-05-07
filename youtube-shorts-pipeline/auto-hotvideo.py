#!/usr/bin/env python3
"""
auto-hotvideo — 蹭热点视频生成工具

独立CLI入口，供Claude Code/OpenClaw等AI工具调用。

用法:
    python auto-hotvideo.py hot              # 获取今日热点
    python auto-hotvideo.py make "主题"      # 生成视频
    python auto-hotvideo.py run              # 全自动：热点→视频
"""

import argparse
import json
import sys
import time
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from verticals.config import CONFIG_FILE, DRAFTS_DIR, MEDIA_DIR
from verticals.log import log


def get_hot_topics(limit: int = 10) -> list:
    """获取热点话题列表"""
    from verticals.topics import fetch_all_hot_sources
    topics = fetch_all_hot_sources()
    return topics[:limit]


def make_video(topic: str, niche: str = "viral", use_video_api: bool = False) -> dict:
    """
    生成视频

    Args:
        topic: 主题内容
        niche: 内容风格 (viral/tech/general)
        use_video_api: 是否使用视频API生成动态场景

    Returns:
        dict: 包含video_path, script, title等信息
    """
    from verticals.draft import generate_draft
    from verticals.broll import generate_broll
    from verticals.tts import generate_voiceover
    from verticals.captions import generate_captions
    from verticals.music import select_and_prepare_music
    from verticals.assemble import assemble_video
    from verticals.state import PipelineState

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    job_id = str(int(time.time()))
    work_dir = MEDIA_DIR / f"work_{job_id}"
    work_dir.mkdir(exist_ok=True)

    result = {
        "job_id": job_id,
        "topic": topic,
        "niche": niche,
    }

    # 1. 生成脚本
    log(f"生成脚本: {topic}")
    draft = generate_draft(topic, "", niche=niche, platform="shorts", viral_mode=True)
    draft["job_id"] = job_id

    # 保存draft
    draft_path = DRAFTS_DIR / f"{job_id}.json"
    state = PipelineState(draft)
    state.complete_stage("research")
    state.complete_stage("draft")
    state.save(draft_path)
    result["draft_path"] = str(draft_path)
    result["script"] = draft.get("script", "")
    result["title"] = draft.get("youtube_title", "")

    # 2. 生成B-roll
    if use_video_api:
        # 使用视频API生成动态场景
        log("使用RunningHub视频API生成动态场景...")
        video_prompts = draft.get("broll_prompts", [])[:3]
        video_path = _generate_video_scenes(video_prompts, work_dir, job_id)
        result["video_path"] = str(video_path)
    else:
        # 使用图片API
        log("生成B-roll图片...")
        frames = generate_broll(draft.get("broll_prompts", ["Cinematic scene"] * 3), work_dir)
        state.complete_stage("broll", {"frames": [str(f) for f in frames]})

    # 3. 生成语音
    log("生成语音...")
    vo_path = generate_voiceover(draft.get("script", ""), work_dir, "zh", provider="dashscope")
    state.complete_stage("voiceover", {"path": str(vo_path)})

    # 4. 生成字幕
    log("生成字幕...")
    captions_result = generate_captions(vo_path, work_dir, "zh")
    state.complete_stage("captions", {
        "srt_path": str(captions_result.get("srt_path", "")),
        "ass_path": str(captions_result.get("ass_path", "")),
    })

    # 5. 准备音乐
    log("准备背景音乐...")
    music_result = select_and_prepare_music(vo_path, work_dir)

    # 6. 合成视频
    log("合成视频...")
    if use_video_api and "video_path" in result:
        # 视频已生成，只需添加音频和字幕
        final_video = _merge_video_audio(
            result["video_path"],
            vo_path,
            captions_result.get("ass_path"),
            music_result.get("track_path"),
            music_result.get("duck_filter"),
            work_dir,
            job_id
        )
    else:
        final_video = assemble_video(
            frames=frames,
            voiceover=vo_path,
            out_dir=work_dir,
            job_id=job_id,
            lang="zh",
            ass_path=captions_result.get("ass_path"),
            music_path=music_result.get("track_path"),
            duck_filter=music_result.get("duck_filter"),
        )

    state.complete_stage("assemble", {"video_path": str(final_video)})
    state.save(draft_path)

    result["video_path"] = str(final_video)
    result["status"] = "success"

    return result


def _generate_video_scenes(prompts: list, work_dir: Path, job_id: str) -> Path:
    """使用RunningHub视频API生成多场景视频"""
    import requests

    from verticals.config import load_config

    cfg = load_config()
    api_key = cfg.get("RUNNINGHUB_API_KEY", "")
    if not api_key:
        raise RuntimeError("RUNNINGHUB_API_KEY未配置")

    submit_url = "https://www.runninghub.cn/openapi/v2/rhart-video-v3.1-fast/text-to-video"
    poll_url = "https://www.runninghub.cn/openapi/v2/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 构建多场景提示词
    scene_desc = "\n".join([f"第{i*2+1}-{i*2+2}秒：{p}" for i, p in enumerate(prompts)])
    full_prompt = f"请生成一段视频，每2秒切换一个场景：\n{scene_desc}\n电影级画质，流畅过渡"

    body = {
        "prompt": full_prompt,
        "aspectRatio": "9:16",
        "seconds": str(len(prompts) * 2),
        "resolution": "720p"
    }

    # 提交任务
    r = requests.post(submit_url, json=body, headers=headers, timeout=30)
    data = r.json()
    task_id = data.get("taskId")

    if not task_id:
        raise RuntimeError(f"视频任务提交失败: {data}")

    log(f"视频任务已提交: {task_id}")

    # 轮询结果
    for i in range(60):
        time.sleep(10)
        pr = requests.post(poll_url, json={"taskId": task_id}, headers=headers, timeout=10)
        pd = pr.json()
        status = pd.get("status")

        if status == "SUCCESS":
            url = pd["results"][0]["url"]
            video_path = work_dir / f"video_{job_id}.mp4"
            video_data = requests.get(url, timeout=60).content
            video_path.write_bytes(video_data)
            log(f"视频生成成功: {video_path}")
            return video_path
        elif status == "FAILED":
            raise RuntimeError(f"视频生成失败: {pd.get('errorMessage')}")

    raise RuntimeError("视频生成超时")


def _merge_video_audio(video_path: Path, audio_path: Path, ass_path: str,
                       music_path: str, duck_filter: str, work_dir: Path, job_id: str) -> Path:
    """合并视频、音频、字幕"""
    import subprocess

    from verticals.assemble import get_audio_duration

    output = MEDIA_DIR / f"verticals_{job_id}_zh.mp4"
    duration = get_audio_duration(audio_path)

    # 构建ffmpeg命令
    cmd = ["ffmpeg", "-i", str(video_path), "-i", str(audio_path)]

    # 音频滤镜
    if music_path:
        music_filter = f"[2:a]aloop=loop=-1:size=2e+09,atrim=0:{duration}"
        if duck_filter:
            music_filter += f",{duck_filter}"
        music_filter += "[music]"
        audio_filter = f"{music_filter};[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        cmd += ["-stream_loop", "-1", "-i", str(music_path), "-filter_complex", audio_filter]
        map_audio = "[aout]"
    else:
        map_audio = "1:a"

    # 视频滤镜（字幕）
    vf_parts = []
    if ass_path:
        escaped_ass = str(ass_path).replace("\\", "\\\\\\\\").replace(":", "\\:").replace("'", "\\\\'")
        vf_parts.append(f"ass={escaped_ass}")

    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]

    cmd += [
        "-map", "0:v", "-map", map_audio,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(output), "-y", "-loglevel", "quiet"
    ]

    subprocess.run(cmd, check=True)
    return output


def cmd_hot(args):
    """热点话题命令"""
    topics = get_hot_topics(args.limit)

    if args.json:
        data = [{"rank": t.rank, "title": t.title, "source": t.source, "heat": t.heat}
                for t in topics]
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"\n今日热点 ({len(topics)}条):\n")
        for t in topics:
            heat = f" [{t.heat}]" if t.heat else ""
            print(f"  {t.rank:2d}. [{t.source}] {t.title}{heat}")


def cmd_make(args):
    """生成视频命令"""
    result = make_video(
        topic=args.topic,
        niche=getattr(args, 'niche', 'viral'),
        use_video_api=getattr(args, 'video', False)
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n视频生成完成!")
        print(f"  主题: {result['topic']}")
        print(f"  标题: {result.get('title', '')}")
        print(f"  视频: {result['video_path']}")


def cmd_run(args):
    """全自动：获取热点并生成视频"""
    from verticals.topics import get_top_hot_topic

    if args.topic:
        topic = args.topic
    else:
        log("获取今日热点...")
        hot = get_top_hot_topic()
        if not hot:
            print("未获取到热点话题")
            sys.exit(1)
        topic = hot.title
        print(f"\n今日热点: {topic} (来源: {hot.source})")

    result = make_video(
        topic=topic,
        niche=getattr(args, 'niche', 'viral'),
        use_video_api=getattr(args, 'video', False)
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n视频生成完成!")
        print(f"  视频: {result['video_path']}")


def main():
    parser = argparse.ArgumentParser(
        prog="auto-hotvideo",
        description="蹭热点视频生成工具 — 自动获取热点并生成短视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s hot                    # 查看今日热点
  %(prog)s hot --json             # JSON格式输出
  %(prog)s make "一人公司"         # 指定主题生成视频
  %(prog)s make "一人公司" --video # 使用视频API生成动态场景
  %(prog)s run                    # 自动获取今日热点并生成视频
  %(prog)s run --video            # 全自动+视频API
        """
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    # hot命令
    p_hot = sub.add_parser("hot", help="获取今日热点话题")
    p_hot.add_argument("--limit", type=int, default=10, help="显示数量")
    p_hot.add_argument("--json", action="store_true", help="JSON格式输出")

    # make命令
    p_make = sub.add_parser("make", help="生成视频")
    p_make.add_argument("topic", help="视频主题")
    p_make.add_argument("--json", action="store_true", help="JSON格式输出")
    p_make.add_argument("--niche", default="viral", help="内容风格")
    p_make.add_argument("--video", action="store_true", help="使用视频API")

    # run命令
    p_run = sub.add_parser("run", help="全自动：热点→视频")
    p_run.add_argument("--topic", help="指定主题")
    p_run.add_argument("--json", action="store_true", help="JSON格式输出")
    p_run.add_argument("--niche", default="viral", help="内容风格")
    p_run.add_argument("--video", action="store_true", help="使用视频API")

    args = parser.parse_args()

    if args.cmd == "hot":
        cmd_hot(args)
    elif args.cmd == "make":
        cmd_make(args)
    elif args.cmd == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
