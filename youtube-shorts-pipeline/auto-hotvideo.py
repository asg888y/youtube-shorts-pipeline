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
import subprocess
import sys
import time
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from verticals.config import CONFIG_FILE, DRAFTS_DIR, MEDIA_DIR
from verticals.log import log

# ffmpeg-full 路径（包含libass字幕滤镜支持）
FFMPEG = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg"
FFPROBE = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffprobe"


def get_hot_topics(limit: int = 10) -> list:
    """获取热点话题列表"""
    from verticals.topics import fetch_all_hot_sources
    topics = fetch_all_hot_sources()
    return topics[:limit]


def make_video(
    topic: str,
    niche: str = "viral",
    use_video_api: bool = False,
    switch_seconds: float = 2.0,
    image_count: int = 3,
    video_count: int = 0,
    start_with_video: bool = False,
) -> dict:
    """
    生成视频

    Args:
        topic: 主题内容
        niche: 内容风格 (viral/tech/general)
        use_video_api: 是否使用视频API生成动态场景
        switch_seconds: 每个场景的展示时长（秒）
        image_count: 图片数量
        video_count: 视频片段数量
        start_with_video: 开头是否使用视频

    Returns:
        dict: 包含video_path, script, title等信息
    """
    from verticals.draft import generate_draft
    from verticals.broll import generate_broll, animate_frame
    from verticals.tts import generate_voiceover
    from verticals.captions import generate_captions
    from verticals.music import select_and_prepare_music
    from verticals.assemble import assemble_video, get_audio_duration
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
        "params": {
            "switch_seconds": switch_seconds,
            "image_count": image_count,
            "video_count": video_count,
            "use_video_api": use_video_api,
            "start_with_video": start_with_video,
        }
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

    prompts = draft.get("broll_prompts", ["Cinematic scene"] * image_count)

    # 2. 生成素材（图片+视频混合）
    video_segments = []
    image_frames = []

    # 根据start_with_video决定开头素材类型
    media_order = []
    if start_with_video and video_count > 0:
        media_order = ["video"] * video_count + ["image"] * image_count
    else:
        media_order = ["image"] * image_count + ["video"] * video_count if video_count > 0 else ["image"] * image_count

    # 生成视频片段（使用RunningHub视频API）
    if video_count > 0:
        log(f"生成{video_count}个视频片段...")
        video_prompts = prompts[:video_count]
        for i, prompt in enumerate(video_prompts):
            video_path = _generate_single_video(prompt, work_dir, job_id, i, switch_seconds)
            video_segments.append(video_path)

    # 生成图片（使用RunningHub图片API）
    image_prompts_needed = image_count
    if image_prompts_needed > 0:
        log(f"生成{image_count}张图片...")
        # 取对应的prompts
        img_prompts = prompts[video_count:video_count + image_count] if video_count > 0 else prompts[:image_count]
        # 补齐
        while len(img_prompts) < image_count:
            img_prompts.append(img_prompts[-1] if img_prompts else "Cinematic scene")
        frames = generate_broll(img_prompts[:image_count], work_dir)
        image_frames = frames
        state.complete_stage("broll", {"frames": [str(f) for f in frames]})

    # 3. 生成语音
    log("生成语音...")
    vo_path = generate_voiceover(draft.get("script", ""), work_dir, "zh", provider="dashscope")
    state.complete_stage("voiceover", {"path": str(vo_path)})
    audio_duration = get_audio_duration(vo_path)

    # 4. 生成字幕
    log("生成字幕...")
    captions_result = generate_captions(vo_path, work_dir, "zh")
    ass_path = captions_result.get("ass_path")
    srt_path = captions_result.get("srt_path")
    state.complete_stage("captions", {
        "srt_path": str(srt_path),
        "ass_path": str(ass_path),
    })

    # 5. 准备音乐
    log("准备背景音乐...")
    music_result = select_and_prepare_music(vo_path, work_dir)
    music_path = music_result.get("track_path")
    duck_filter = music_result.get("duck_filter")

    # 6. 合成视频（使用switch_seconds控制切换节奏）
    log("合成视频...")

    # 计算总素材数和总时长
    total素材 = len(video_segments) + len(image_frames)
    total_duration_needed = total素材 * switch_seconds

    # 如果音频时长不足，循环音频；如果音频时长过长，截断
    log(f"音频时长: {audio_duration}s, 目标时长: {total_duration_needed}s (素材数:{total素材}, 切换:{switch_seconds}s)")

    # 合成策略：混合视频片段和图片动画
    final_video = _assemble_mixed(
        video_segments=video_segments,
        image_frames=image_frames,
        media_order=media_order,
        vo_path=vo_path,
        ass_path=ass_path,
        music_path=music_path,
        duck_filter=duck_filter,
        work_dir=work_dir,
        job_id=job_id,
        switch_seconds=switch_seconds,
        audio_duration=audio_duration,
    )

    state.complete_stage("assemble", {"video_path": str(final_video)})
    state.save(draft_path)

    result["video_path"] = str(final_video)
    result["ass_path"] = str(ass_path)
    result["music_path"] = str(music_path)
    result["status"] = "success"

    return result


def _generate_single_video(prompt: str, work_dir: Path, job_id: str, index: int, duration: float) -> Path:
    """生成单个视频片段"""
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

    # 视频时长必须是4/6/8秒
    valid_durations = [4, 6, 8]
    video_seconds = min(valid_durations, key=lambda x: abs(x - duration))
    if video_seconds < duration:
        video_seconds = max(valid_durations)

    full_prompt = f"请生成一段{video_seconds}秒视频：{prompt}。电影级画质，流畅运动。"

    body = {
        "prompt": full_prompt,
        "aspectRatio": "9:16",
        "seconds": str(video_seconds),
        "resolution": "720p"
    }

    log(f"  提交视频任务 {index+1}: {prompt[:30]}...")
    r = requests.post(submit_url, json=body, headers=headers, timeout=30)
    data = r.json()
    task_id = data.get("taskId")

    if not task_id:
        raise RuntimeError(f"视频任务提交失败: {data}")

    # 轮询结果
    for i in range(60):
        time.sleep(10)
        pr = requests.post(poll_url, json={"taskId": task_id}, headers=headers, timeout=10)
        pd = pr.json()
        status = pd.get("status")

        if status == "SUCCESS":
            url = pd["results"][0]["url"]
            video_path = work_dir / f"video_{job_id}_{index}.mp4"
            video_data = requests.get(url, timeout=60).content
            video_path.write_bytes(video_data)
            log(f"  视频片段 {index+1} 生成成功")
            return video_path
        elif status == "FAILED":
            raise RuntimeError(f"视频生成失败: {pd.get('errorMessage')}")

    raise RuntimeError("视频生成超时")


def _assemble_mixed(
    video_segments: list,
    image_frames: list,
    media_order: list,
    vo_path: Path,
    ass_path: str,
    music_path: str,
    duck_filter: str,
    work_dir: Path,
    job_id: str,
    switch_seconds: float,
    audio_duration: float,
) -> Path:
    """混合合成视频片段和图片动画"""

    from verticals.broll import animate_frame
    from verticals.config import VIDEO_WIDTH, VIDEO_HEIGHT

    output = MEDIA_DIR / f"verticals_{job_id}_zh.mp4"

    # 生成所有动画片段
    animated_segments = []
    effects = ["zoom_in", "pan_right", "zoom_out"]

    video_idx = 0
    image_idx = 0

    for i, kind in enumerate(media_order):
        seg_path = work_dir / f"seg_{i}.mp4"

        if kind == "video" and video_idx < len(video_segments):
            # 视频片段：调整时长
            src_video = video_segments[video_idx]
            video_idx += 1
            # 截取或循环到switch_seconds时长
            _adjust_video_duration(src_video, seg_path, switch_seconds)
        else:
            # 图片：生成Ken Burns动画
            if image_idx < len(image_frames):
                src_image = image_frames[image_idx]
                image_idx += 1
            else:
                # fallback纯色
                from PIL import Image
                colors = [(20, 20, 60), (40, 10, 40), (10, 30, 50)]
                src_image = work_dir / f"fallback_{i}.png"
                img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), colors[i % len(colors)])
                img.save(src_image)
            animate_frame(src_image, seg_path, switch_seconds, effects[i % len(effects)])

        animated_segments.append(seg_path)

    # 拼接所有片段
    concat_file = work_dir / "concat.txt"
    def _esc(p):
        return str(p).replace("'", "'\\''")
    concat_file.write_text("\n".join(f"file '{_esc(p)}'" for p in animated_segments))

    merged_video = work_dir / "merged_video.mp4"
    subprocess.run([
        FFMPEG, "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(merged_video), "-y", "-loglevel", "quiet",
    ], check=True)

    # 合成最终视频：视频+语音+字幕+音乐
    cmd = [FFMPEG, "-i", str(merged_video), "-i", str(vo_path)]

    # 音频处理
    if music_path:
        music_filter = f"[2:a]aloop=loop=-1:size=2e+09,atrim=0:{audio_duration}"
        if duck_filter:
            music_filter += f",{duck_filter}"
        music_filter += "[music]"
        audio_filter = f"{music_filter};[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        cmd += ["-stream_loop", "-1", "-i", str(music_path), "-filter_complex", audio_filter]
        map_audio = "[aout]"
    else:
        map_audio = "1:a"

    # 字幕滤镜（正确转义）
    vf_parts = []
    if ass_path and Path(ass_path).exists():
        # ffmpeg ass滤镜路径转义规则
        escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")
        vf_parts.append(f"ass='{escaped_ass}'")

    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]

    cmd += [
        "-map", "0:v", "-map", map_audio,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(output), "-y"
    ]

    log(f"执行ffmpeg合成...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ffmpeg错误: {result.stderr[:500]}")
        # 尝试不带字幕合成
        log("尝试不带字幕合成...")
        cmd_no_sub = [FFMPEG, "-i", str(merged_video), "-i", str(vo_path)]
        if music_path:
            cmd_no_sub += ["-stream_loop", "-1", "-i", str(music_path), "-filter_complex", audio_filter]
            cmd_no_sub += ["-map", "0:v", "-map", "[aout]"]
        else:
            cmd_no_sub += ["-map", "0:v", "-map", "1:a"]
        cmd_no_sub += [
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            str(output), "-y"
        ]
        subprocess.run(cmd_no_sub, check=True)

    log(f"视频合成完成: {output}")
    return output


def _adjust_video_duration(src_path: Path, out_path: Path, target_duration: float):
    """调整视频片段时长到目标时长"""
    # 获取原视频时长
    result = subprocess.run([
        FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(src_path)
    ], capture_output=True, text=True)
    src_duration = float(result.stdout.strip())

    if src_duration >= target_duration:
        # 截取
        subprocess.run([
            FFMPEG, "-i", str(src_path), "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(out_path), "-y", "-loglevel", "quiet"
        ], check=True)
    else:
        # 循环
        subprocess.run([
            FFMPEG, "-stream_loop", "-1", "-i", str(src_path), "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(out_path), "-y", "-loglevel", "quiet"
        ], check=True)


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
        use_video_api=getattr(args, 'video', False),
        switch_seconds=getattr(args, 'switch', 2.0),
        image_count=getattr(args, 'images', 3),
        video_count=getattr(args, 'videos', 0),
        start_with_video=getattr(args, 'start_video', False),
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
        use_video_api=getattr(args, 'video', False),
        switch_seconds=getattr(args, 'switch', 2.0),
        image_count=getattr(args, 'images', 3),
        video_count=getattr(args, 'videos', 0),
        start_with_video=getattr(args, 'start_video', False),
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n视频生成完成!")
        print(f"  视频: {result['video_path']}")

    # 自动打开视频
    subprocess.run(["open", result['video_path']])


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
  %(prog)s make "一人公司" --switch 3 --images 5 --videos 2  # 自定义参数
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
    p_make.add_argument("--switch", type=float, default=2.0, help="场景切换时长(秒)")
    p_make.add_argument("--images", type=int, default=3, help="图片数量")
    p_make.add_argument("--videos", type=int, default=0, help="视频片段数量")
    p_make.add_argument("--start-video", action="store_true", help="开头使用视频")

    # run命令
    p_run = sub.add_parser("run", help="全自动：热点→视频")
    p_run.add_argument("--topic", help="指定主题")
    p_run.add_argument("--json", action="store_true", help="JSON格式输出")
    p_run.add_argument("--niche", default="viral", help="内容风格")
    p_run.add_argument("--video", action="store_true", help="使用视频API")
    p_run.add_argument("--switch", type=float, default=2.0, help="场景切换时长(秒)")
    p_run.add_argument("--images", type=int, default=3, help="图片数量")
    p_run.add_argument("--videos", type=int, default=0, help="视频片段数量")
    p_run.add_argument("--start-video", action="store_true", help="开头使用视频")

    args = parser.parse_args()

    if args.cmd == "hot":
        cmd_hot(args)
    elif args.cmd == "make":
        cmd_make(args)
    elif args.cmd == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()