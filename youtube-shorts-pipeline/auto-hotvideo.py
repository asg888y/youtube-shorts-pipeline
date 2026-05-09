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
import math
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from verticals.config import CONFIG_FILE, DRAFTS_DIR, MEDIA_DIR, load_config, save_config
from verticals.log import log

# ffmpeg-full 路径（包含libass字幕滤镜支持）
FFMPEG = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg"
FFPROBE = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffprobe"

# 成本常量（仅限当前模型，禁止切换！）
COST_PER_IMAGE = 0.05  # rhart-image-v1
COST_PER_VIDEO = 0.20  # rhart-video-v3.1-fast
MAX_RETRY_COUNT = 3     # 最大重试次数


def get_hot_topics(limit: int = 10) -> list:
    """获取热点话题列表"""
    from verticals.topics import fetch_all_hot_sources
    topics = fetch_all_hot_sources()
    return topics[:limit]


def is_approval_required() -> bool:
    """检查是否需要审批"""
    cfg = load_config()
    return cfg.get("APPROVAL_REQUIRED", True)


def calculate_cost(image_count: int, video_count: int) -> dict:
    """计算素材生成成本"""
    image_cost = image_count * COST_PER_IMAGE
    video_cost = video_count * COST_PER_VIDEO
    total_cost = image_cost + video_cost
    return {
        "image_count": image_count,
        "video_count": video_count,
        "image_cost": image_cost,
        "video_cost": video_cost,
        "total_cost": total_cost,
    }


def request_approval(image_count: int, video_count: int, is_retry: bool = False, retry_info: dict = None) -> dict:
    """
    请求素材生成审批

    Returns:
        dict: {"approved": bool, "message": str}
    """
    if is_retry and retry_info:
        # 重试申请
        cost = calculate_cost(
            retry_info.get("failed_images", 0),
            retry_info.get("failed_videos", 0)
        )
        return {
            "approved": False,
            "need_approval": True,
            "message": f"""素材生成失败，需要重试：
- 图片：{cost['image_count']}张失败 × ${COST_PER_IMAGE} = ${cost['image_cost']:.2f}
- 视频：{cost['video_count']}个失败 × ${COST_PER_VIDEO} = ${cost['video_cost']:.2f}
- 重试成本：${cost['total_cost']:.2f}

请回复"同意"确认重试，其他任何回复均取消："""
        }
    else:
        # 首次申请
        cost = calculate_cost(image_count, video_count)
        return {
            "approved": False,
            "need_approval": True,
            "message": f"""素材生成申请：
- 图片：{image_count}张 × ${COST_PER_IMAGE} = ${cost['image_cost']:.2f}
- 视频：{video_count}个 × ${COST_PER_VIDEO} = ${cost['video_cost']:.2f}
- 预估总成本：${cost['total_cost']:.2f}

请回复"同意"确认生成，其他任何回复均取消："""
        }


def save_task_state(job_id: str, topic: str, stage: str, stages: dict, params: dict):
    """保存任务状态"""
    work_dir = MEDIA_DIR / f"work_{job_id}"
    work_dir.mkdir(exist_ok=True)
    state_file = work_dir / "state.json"
    state = {
        "job_id": job_id,
        "topic": topic,
        "stage": stage,
        "stages": stages,
        "params": params,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
    }
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def load_task_state(job_id: str) -> dict:
    """加载任务状态"""
    state_file = MEDIA_DIR / f"work_{job_id}" / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return None


def generate_broll_prompts_from_script(script: str, count: int, niche: str = "general") -> list:
    """从文案生成B-roll提示词"""
    from verticals.llm import call_llm

    prompt = f"""根据以下文案内容，生成{count}个视觉画面描述，用于AI生成图片。

文案：
{script}

要求：
1. 每个画面描述要具体、视觉化
2. 画面要与文案内容相关
3. 风格统一，适合短视频
4. 每个描述一行，不要编号

直接输出{count}行画面描述："""

    try:
        result = call_llm(prompt, max_tokens=500)
        prompts = [p.strip() for p in result.strip().split('\n') if p.strip()]
        # 确保数量正确
        while len(prompts) < count:
            prompts.append("Cinematic scene, dramatic lighting")
        return prompts[:count]
    except Exception as e:
        log(f"生成B-roll提示词失败: {e}")
        return ["Cinematic scene, dramatic lighting"] * count


def find_incomplete_tasks() -> list:
    """查找未完成的任务"""
    incomplete = []
    for work_dir in MEDIA_DIR.glob("work_*"):
        state_file = work_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            if state.get("stage") not in ["completed", "failed"]:
                incomplete.append(state)
    return incomplete


def make_video(
    topic: str,
    niche: str = "multi_empty_bureau",
    use_video_api: bool = False,
    switch_seconds: float = 2.0,
    image_count: int = 3,
    video_count: int = 0,
    start_with_video: bool = False,
    skip_approval: bool = False,
    direct_script: str = None,
    script_source: str = "hot",
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
        skip_approval: 是否跳过审批（用于已获批准的继续执行）
        direct_script: 直接输入的文案（跳过热点改写）
        script_source: 文案来源（hot/direct/transcribe）

    Returns:
        dict: 包含video_path, script, title等信息，或需要审批的信息
    """
    from verticals.draft import generate_draft
    from verticals.broll import generate_broll, animate_frame
    from verticals.tts import generate_voiceover
    from verticals.captions import generate_captions
    from verticals.music import select_and_prepare_music
    from verticals.assemble import assemble_video, get_audio_duration
    from verticals.state import PipelineState

    # 如果是视频链接，先转录
    if script_source == "transcribe" and direct_script:
        from verticals.video_transcriber import transcribe_video
        log(f"转录视频链接: {direct_script}")
        transcribe_result = transcribe_video(direct_script)
        if transcribe_result['success']:
            direct_script = transcribe_result['transcript']
            script_source = "direct"
            log(f"转录成功: {len(direct_script)}字, 时长{transcribe_result['duration']:.1f}秒")
        else:
            return {
                "status": "error",
                "error": f"视频转录失败: {transcribe_result.get('error', 'unknown')}"
            }

    # 检查是否需要审批
    if not skip_approval and is_approval_required():
        approval = request_approval(image_count, video_count)
        return {
            "status": "need_approval",
            "need_approval": True,
            "message": approval["message"],
            "params": {
                "topic": topic,
                "niche": niche,
                "use_video_api": use_video_api,
                "switch_seconds": switch_seconds,
                "image_count": image_count,
                "video_count": video_count,
                "start_with_video": start_with_video,
            }
        }

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    job_id = str(int(time.time()))
    work_dir = MEDIA_DIR / f"work_{job_id}"
    work_dir.mkdir(exist_ok=True)

    params = {
        "switch_seconds": switch_seconds,
        "image_count": image_count,
        "video_count": video_count,
        "use_video_api": use_video_api,
        "start_with_video": start_with_video,
    }

    result = {
        "job_id": job_id,
        "topic": topic,
        "niche": niche,
        "params": params
    }

    # 初始化状态
    stages = {
        "draft": {"status": "pending"},
        "voiceover": {"status": "pending"},
        "broll": {"status": "pending"},
        "captions": {"status": "pending"},
        "assemble": {"status": "pending"},
    }
    save_task_state(job_id, topic, "draft", stages, params)

    # 1. 生成脚本
    stages["draft"]["status"] = "in_progress"
    save_task_state(job_id, topic, "draft", stages, params)

    # 根据文案来源决定生成方式
    if script_source == "direct" and direct_script:
        # 直接使用用户输入的文案
        log(f"使用直接输入的文案: {direct_script[:50]}...")
        script = direct_script
        title = topic if topic else "短视频"
        prompts = generate_broll_prompts_from_script(script, image_count, niche)
        draft = {
            "job_id": job_id,
            "script": script,
            "youtube_title": title,
            "broll_prompts": prompts,
        }
    else:
        # 从热点生成脚本
        log(f"生成脚本: {topic}")
        draft = generate_draft(topic, "", niche=niche, platform="shorts", viral_mode=False)
        draft["job_id"] = job_id

    # 保存draft
    draft_path = DRAFTS_DIR / f"{job_id}.json"
    state = PipelineState(draft)
    state.complete_stage("research")
    state.complete_stage("draft")
    state.save(draft_path)

    stages["draft"]["status"] = "completed"
    stages["draft"]["output"] = str(draft_path)
    save_task_state(job_id, topic, "voiceover", stages, params)

    result["draft_path"] = str(draft_path)
    result["script"] = draft.get("script", "")
    result["title"] = draft.get("youtube_title", "")

    prompts = draft.get("broll_prompts", ["Cinematic scene"] * image_count)

    # 素材数量校验和自动补充
    script_text = draft.get("script", "")
    if script_text:
        # 估算音频时长（中文约3-4字/秒）
        estimated_duration = len(script_text) / 3.5
        required_images = math.ceil(estimated_duration / switch_seconds)

        if image_count < required_images:
            log(f"")
            log(f"⚠️  素材数量不足警告")
            log(f"   文案长度: {len(script_text)}字")
            log(f"   预估时长: {estimated_duration:.0f}秒")
            log(f"   切换间隔: {switch_seconds}秒")
            log(f"   当前图片: {image_count}张")
            log(f"   建议图片: {required_images}张")
            log(f"   当前每张图片将播放: {estimated_duration/image_count:.1f}秒")
            log(f"")

            # 自动补充素材数量
            log(f"✅ 自动调整素材数量: {image_count} → {required_images}张")
            image_count = required_images

            # 补充 prompts
            while len(prompts) < image_count:
                prompts.append(f"Cinematic scene, dramatic lighting, style {len(prompts)+1}")

            # 更新 params
            params["image_count"] = image_count

    # 2. 生成素材（图片+视频混合）
    video_segments = []
    image_frames = []
    failed_images = 0
    failed_videos = 0

    # 根据start_with_video决定开头素材类型
    media_order = []
    if start_with_video and video_count > 0:
        media_order = ["video"] * video_count + ["image"] * image_count
    else:
        media_order = ["image"] * image_count + ["video"] * video_count if video_count > 0 else ["image"] * image_count

    stages["broll"]["status"] = "in_progress"
    stages["broll"]["total"] = image_count + video_count
    stages["broll"]["completed"] = 0
    save_task_state(job_id, topic, "broll", stages, params)

    # 生成视频片段（使用RunningHub视频API）
    if video_count > 0:
        log(f"生成{video_count}个视频片段...")
        video_prompts = prompts[:video_count]
        for i, prompt in enumerate(video_prompts):
            try:
                video_path = _generate_single_video(prompt, work_dir, job_id, i, switch_seconds)
                video_segments.append(video_path)
                stages["broll"]["completed"] = i + 1
                save_task_state(job_id, topic, "broll", stages, params)
            except Exception as e:
                log(f"视频片段 {i+1} 生成失败: {e}")
                failed_videos += 1

    # 生成图片（使用RunningHub图片API）
    if image_count > 0:
        log(f"生成{image_count}张图片...")
        img_prompts = prompts[video_count:video_count + image_count] if video_count > 0 else prompts[:image_count]
        while len(img_prompts) < image_count:
            img_prompts.append(img_prompts[-1] if img_prompts else "Cinematic scene")

        try:
            frames = generate_broll(img_prompts[:image_count], work_dir)
            image_frames = frames
            # 检查是否全部成功
            actual_count = len([f for f in frames if not f.name.startswith("fallback_")])
            failed_images = image_count - actual_count
            stages["broll"]["completed"] = len(video_segments) + len(frames)
            save_task_state(job_id, topic, "broll", stages, params)
        except Exception as e:
            log(f"图片生成失败: {e}")
            failed_images = image_count

    # 检查是否有失败需要重试
    if (failed_images > 0 or failed_videos > 0) and is_approval_required():
        stages["broll"]["status"] = "failed"
        stages["broll"]["failed_images"] = failed_images
        stages["broll"]["failed_videos"] = failed_videos
        save_task_state(job_id, topic, "broll", stages, params)

        retry_approval = request_approval(0, 0, is_retry=True, retry_info={
            "failed_images": failed_images,
            "failed_videos": failed_videos,
        })
        return {
            "status": "need_retry",
            "need_approval": True,
            "message": retry_approval["message"],
            "job_id": job_id,
            "failed_images": failed_images,
            "failed_videos": failed_videos,
        }

    stages["broll"]["status"] = "completed"
    save_task_state(job_id, topic, "voiceover", stages, params)

    # 3. 生成语音
    log("生成语音...")
    stages["voiceover"]["status"] = "in_progress"
    save_task_state(job_id, topic, "voiceover", stages, params)

    vo_path = generate_voiceover(draft.get("script", ""), work_dir, "zh", provider="dashscope")

    stages["voiceover"]["status"] = "completed"
    stages["voiceover"]["output"] = str(vo_path)
    save_task_state(job_id, topic, "captions", stages, params)

    audio_duration = get_audio_duration(vo_path)

    # 4. 生成字幕
    log("生成字幕...")
    stages["captions"]["status"] = "in_progress"
    save_task_state(job_id, topic, "captions", stages, params)

    captions_result = generate_captions(vo_path, work_dir, "zh")
    ass_path = captions_result.get("ass_path")
    srt_path = captions_result.get("srt_path")

    stages["captions"]["status"] = "completed"
    stages["captions"]["output"] = str(ass_path) if ass_path else None
    save_task_state(job_id, topic, "assemble", stages, params)

    # 5. 准备音乐
    log("准备背景音乐...")
    music_result = select_and_prepare_music(vo_path, work_dir)
    music_path = music_result.get("track_path")
    duck_filter = music_result.get("duck_filter")

    # 6. 合成视频（使用switch_seconds控制切换节奏）
    log("合成视频...")
    stages["assemble"]["status"] = "in_progress"
    save_task_state(job_id, topic, "assemble", stages, params)

    # 计算总素材数和总时长
    total素材 = len(video_segments) + len(image_frames)
    total_duration_needed = total素材 * switch_seconds

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

    stages["assemble"]["status"] = "completed"
    stages["assemble"]["output"] = str(final_video)
    save_task_state(job_id, topic, "completed", stages, params)

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

    # 视频时长固定8秒（API上限，不可超8秒）
    video_seconds = 8

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
    # 尝试从状态文件读取直接文案
    state_file = Path.home() / ".openclaw" / "memory" / "auto-hotvideo-state.json"
    direct_script = None
    script_source = "hot"

    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            direct_script = state.get("params", {}).get("direct_script")
            script_source = state.get("script_source", "hot")
        except:
            pass

    result = make_video(
        topic=args.topic,
        niche=getattr(args, 'niche', 'multi_empty_bureau'),
        use_video_api=getattr(args, 'video', False),
        switch_seconds=getattr(args, 'switch', 2.0),
        image_count=getattr(args, 'images', 3),
        video_count=getattr(args, 'videos', 0),
        start_with_video=getattr(args, 'start_video', False),
        skip_approval=getattr(args, 'skip_approval', False),
        direct_script=direct_script,
        script_source=script_source,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("status") == "need_approval":
            print(result["message"])
        elif result.get("status") == "need_retry":
            print(result["message"])
        else:
            print(f"\n视频生成完成!")
            print(f"  主题: {result['topic']}")
            print(f"  标题: {result.get('title', '')}")
            print(f"  视频: {result['video_path']}")


def cmd_continue(args):
    """继续未完成任务"""
    incomplete = find_incomplete_tasks()

    if not incomplete:
        print("没有未完成的任务")
        return

    if len(incomplete) == 1:
        task = incomplete[0]
    else:
        print("发现多个未完成任务：\n")
        for i, task in enumerate(incomplete, 1):
            print(f"  {i}. [{task['job_id']}] {task['topic']} - {task['stage']}")
        print(f"\n请指定任务ID: python auto-hotvideo.py continue <job_id>")
        return

    print(f"继续任务: {task['job_id']}")
    print(f"  主题: {task['topic']}")
    print(f"  当前进度: {task['stage']}")

    # 显示阶段进度
    stages = task.get("stages", {})
    for stage_name, stage_info in stages.items():
        status = stage_info.get("status", "pending")
        status_icon = "✅" if status == "completed" else "⏳" if status == "in_progress" else "⏸️"
        print(f"  {status_icon} {stage_name}: {status}")

    # TODO: 实现从中断点恢复的逻辑
    print("\n提示：请使用相同参数重新执行 make 命令，并添加 --skip-approval 跳过审批")


def cmd_status(args):
    """查看任务状态"""
    if args.job_id:
        state = load_task_state(args.job_id)
        if not state:
            print(f"任务 {args.job_id} 不存在")
            return
        states = [state]
    else:
        states = find_incomplete_tasks()

    if not states:
        print("没有进行中的任务")
        return

    for state in states:
        print(f"\n任务: {state['job_id']}")
        print(f"  主题: {state['topic']}")
        print(f"  当前阶段: {state['stage']}")
        print(f"  更新时间: {state.get('updated', 'unknown')}")

        stages = state.get("stages", {})
        for stage_name, stage_info in stages.items():
            status = stage_info.get("status", "pending")
            print(f"    - {stage_name}: {status}")


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
        niche=getattr(args, 'niche', 'multi_empty_bureau'),
        use_video_api=getattr(args, 'video', False),
        switch_seconds=getattr(args, 'switch', 2.0),
        image_count=getattr(args, 'images', 3),
        video_count=getattr(args, 'videos', 0),
        start_with_video=getattr(args, 'start_video', False),
        skip_approval=getattr(args, 'skip_approval', False),
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("status") == "need_approval":
            print(result["message"])
        elif result.get("status") == "need_retry":
            print(result["message"])
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
  %(prog)s make "一人公司" --skip-approval  # 跳过审批
  %(prog)s run                    # 自动获取今日热点并生成视频
  %(prog)s run --video            # 全自动+视频API
  %(prog)s status                 # 查看任务状态
  %(prog)s continue               # 继续未完成任务
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
    p_make.add_argument("--niche", default="multi_empty_bureau", help="内容风格")
    p_make.add_argument("--video", action="store_true", help="使用视频API")
    p_make.add_argument("--switch", type=float, default=2.0, help="场景切换时长(秒)")
    p_make.add_argument("--images", type=int, default=3, help="图片数量")
    p_make.add_argument("--videos", type=int, default=0, help="视频片段数量")
    p_make.add_argument("--start-video", action="store_true", help="开头使用视频")
    p_make.add_argument("--skip-approval", action="store_true", help="跳过审批")

    # run命令
    p_run = sub.add_parser("run", help="全自动：热点→视频")
    p_run.add_argument("--topic", help="指定主题")
    p_run.add_argument("--json", action="store_true", help="JSON格式输出")
    p_run.add_argument("--niche", default="multi_empty_bureau", help="内容风格")
    p_run.add_argument("--video", action="store_true", help="使用视频API")
    p_run.add_argument("--switch", type=float, default=2.0, help="场景切换时长(秒)")
    p_run.add_argument("--images", type=int, default=3, help="图片数量")
    p_run.add_argument("--videos", type=int, default=0, help="视频片段数量")
    p_run.add_argument("--start-video", action="store_true", help="开头使用视频")
    p_run.add_argument("--skip-approval", action="store_true", help="跳过审批")

    # status命令
    p_status = sub.add_parser("status", help="查看任务状态")
    p_status.add_argument("job_id", nargs="?", help="任务ID")

    # continue命令
    p_continue = sub.add_parser("continue", help="继续未完成任务")

    args = parser.parse_args()

    if args.cmd == "hot":
        cmd_hot(args)
    elif args.cmd == "make":
        cmd_make(args)
    elif args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "continue":
        cmd_continue(args)


if __name__ == "__main__":
    main()