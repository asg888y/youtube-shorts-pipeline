"""本地素材测试脚本 - 不调用任何API，使用已有素材合成视频"""
import subprocess
import json
from pathlib import Path
import time

LOCAL_ASSETS = Path(__file__).parent.parent / "local_assets"
OUTPUT_DIR = Path.home() / ".verticals" / "media"

def run_cmd(cmd, check=True):
    subprocess.run(cmd, check=check, capture_output=True)

def get_audio_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())

def main():
    job_id = str(int(time.time()))
    work_dir = OUTPUT_DIR / f"work_local_{job_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 使用本地图片
    images_dir = LOCAL_ASSETS / "images"
    images = sorted(images_dir.glob("broll_*.png"))
    print(f"图片: {len(images)} 张")

    # 使用本地音频
    voiceover = LOCAL_ASSETS / "audio" / "voiceover_en.mp3"
    print(f"语音: {voiceover.name}")

    # 使用本地音乐
    music = LOCAL_ASSETS / "music" / "free_1778130490.mp3"
    print(f"音乐: {music.name}")

    duration = get_audio_duration(voiceover)
    print(f"时长: {duration:.1f}秒")

    # 1. Ken Burns动画
    per_frame = duration / len(images)
    effects = ["zoom_in", "pan_right", "zoom_out"]
    animated = []

    for i, img in enumerate(images):
        anim = work_dir / f"anim_{i}.mp4"
        fps = 30
        frames = int(per_frame * fps)
        w, h = 1080, 1920

        if effects[i] == "zoom_in":
            vf = f"scale={int(w*1.12)}:{int(h*1.12)},zoompan=z='1.12-0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}"
        elif effects[i] == "pan_right":
            vf = f"scale={int(w*1.15)}:{int(h*1.15)},zoompan=z=1.15:x='0.15*iw*on/{frames}':y='ih*0.075':d={frames}:s={w}x{h}:fps={fps}"
        else:
            vf = f"scale={int(w*1.12)}:{int(h*1.12)},zoompan=z='1.0+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}"

        print(f"  动画 {i+1}/3...")
        run_cmd([
            "ffmpeg", "-loop", "1", "-i", str(img),
            "-vf", vf, "-t", str(per_frame + 0.1), "-r", str(fps),
            "-pix_fmt", "yuv420p", str(anim), "-y", "-loglevel", "quiet"
        ])
        animated.append(anim)

    # 2. 拼接视频
    concat_file = work_dir / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p}'" for p in animated))
    merged = work_dir / "merged.mp4"
    print("拼接视频...")
    run_cmd([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        str(merged), "-y", "-loglevel", "quiet"
    ])

    # 3. Whisper生成字幕
    print("生成字幕...")
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(str(voiceover), word_timestamps=True)

    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            words.append({"word": w["word"].strip(), "start": w["start"], "end": w["end"]})

    print(f"  词数: {len(words)}")

    # 生成ASS字幕
    ass_path = work_dir / "captions.ass"
    margin_v = 480  # 25% from bottom

    ass_content = f"""[Script Info]
Title: Local Test
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,3,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def format_time(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        cs = int((s % 1) * 100)
        return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

    # 每组4个词
    group_size = 4
    for g in range(0, len(words), group_size):
        group = words[g:g+group_size]
        if not group:
            continue
        for active_idx, active_word in enumerate(group):
            text_parts = []
            for j, w in enumerate(group):
                if j == active_idx:
                    text_parts.append(f"{{\\c&H0000FFFF&\\b1\\fs80}}{w['word']}{{\\r}}")
                else:
                    text_parts.append(w["word"])
            text = " ".join(text_parts)
            ass_content += f"Dialogue: 0,{format_time(active_word['start'])},{format_time(active_word['end'])},Default,,0,0,0,,{text}\n"

    ass_path.write_text(ass_content)
    print(f"  字幕: {ass_path.name}")

    # 4. 合成最终视频（视频+语音+字幕+音乐）
    output = OUTPUT_DIR / f"local_test_{job_id}.mp4"

    # 音乐ducking filter
    duck_filter = f"[2:a]aloop=loop=-1:size=2e+09,atrim=0:{duration},volume=0.12[music];[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"

    escaped_ass = str(ass_path).replace("'", "'\\''")

    print("合成最终视频...")
    run_cmd([
        "ffmpeg",
        "-i", str(merged),      # 0: 视频
        "-i", str(voiceover),   # 1: 语音
        "-stream_loop", "-1", "-i", str(music),  # 2: 音乐
        "-filter_complex", duck_filter,
        "-vf", f"ass='{escaped_ass}'",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output), "-y", "-loglevel", "quiet"
    ])

    print(f"\n完成: {output}")
    print(f"时长: {get_audio_duration(output):.1f}秒")

    # 验证
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", str(output)],
        capture_output=True, text=True
    )
    streams = r.stdout.strip().split("\n")
    print(f"流: {streams}")

    return output

if __name__ == "__main__":
    main()