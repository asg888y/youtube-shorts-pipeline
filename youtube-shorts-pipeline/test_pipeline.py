#!/usr/bin/env python3
"""
热点视频管线测试脚本
遍历所有错误可能性，验证逻辑关系
"""

import json
import sys
import traceback
from pathlib import Path

# 添加项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from verticals.log import log

# 测试结果记录
results = {"passed": [], "failed": []}

def test(name: str, func):
    """运行测试并记录结果"""
    try:
        func()
        results["passed"].append(name)
        print(f"✅ {name}")
    except Exception as e:
        results["failed"].append({"name": name, "error": str(e)})
        print(f"❌ {name}: {e}")

# ============================================
# 1. 配置文件加载测试
# ============================================
print("\n" + "="*50)
print("1. 配置文件加载测试")
print("="*50)

def test_load_config():
    from verticals.config import load_config
    cfg = load_config()
    assert cfg is not None, "配置不能为空"
    assert "RUNNINGHUB_API_KEY" in cfg or cfg.get("DASHSCOPE_API_KEY"), "缺少必要API密钥"
test("加载配置文件", test_load_config)

def test_keychain():
    from verticals.keychain_manager import get_key, list_keys
    keys = list_keys()
    assert keys is not None, "Keychain列表不能为空"
test("Keychain密钥管理", test_keychain)

# ============================================
# 2. 风格配置加载测试
# ============================================
print("\n" + "="*50)
print("2. 风格配置加载测试")
print("="*50)

def test_all_niches():
    from verticals.niche import load_niche, get_visual_context, get_script_context
    niches = ["general", "viral", "emotion", "knowledge", "horror", "tech", "business"]
    for niche in niches:
        profile = load_niche(niche)
        assert profile is not None, f"{niche} 配置加载失败"
        visual = get_visual_context(profile)
        script = get_script_context(profile)
        assert visual is not None, f"{niche} visual配置为空"
        assert script is not None, f"{niche} script配置为空"
test("加载所有风格配置", test_all_niches)

def test_scene_modes():
    from verticals.niche import load_niche, get_scene_modes, get_scene_keywords, get_scene_style
    # 测试有scene_modes的风格
    for niche in ["viral", "business"]:
        profile = load_niche(niche)
        scene_config = get_scene_modes(profile)
        assert scene_config is not None, f"{niche} scene_modes为空"
        keywords = get_scene_keywords(profile)
        style = get_scene_style(profile)
        print(f"  {niche}: scene_modes={scene_config.get('enabled')}, keywords={len(keywords) if keywords else 0}")
test("场景模式配置", test_scene_modes)

# ============================================
# 3. 素材库验证测试
# ============================================
print("\n" + "="*50)
print("3. 素材库验证测试")
print("="*50)

def test_local_assets():
    from verticals.broll import get_available_niches, _get_local_frames
    niches = get_available_niches()
    print(f"  可用风格: {niches}")
    assert len(niches) >= 7, f"风格数量不足: {len(niches)}"
    
    for niche in niches:
        frames = _get_local_frames(niche=niche)
        print(f"  {niche}: {len(frames)}张素材")
        assert len(frames) >= 20, f"{niche}素材不足20张"
test("本地素材库", test_local_assets)

def test_fallback_frames():
    from verticals.broll import _fallback_frame
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for niche in ["general", "viral", "emotion", "business"]:
            for i in range(3):
                frame = _fallback_frame(i, Path(tmpdir), niche=niche)
                assert frame.exists(), f"fallback帧不存在: {frame}"
test("Fallback素材生成", test_fallback_frames)

# ============================================
# 4. LLM调用测试
# ============================================
print("\n" + "="*50)
print("4. LLM调用测试")
print("="*50)

def test_llm_provider():
    from verticals.llm import get_provider
    provider = get_provider()
    print(f"  当前LLM提供商: {provider}")
    assert provider in ["minimax", "claude", "gemini", "openai", "dashscope", "xunfei"], f"未知提供商: {provider}"
test("LLM提供商检测", test_llm_provider)

def test_llm_call():
    from verticals.llm import call_llm
    result = call_llm("回复'OK'两个字，不要其他内容", max_tokens=50)
    print(f"  LLM返回: {result[:50]}")
    assert result and len(result) > 0, "LLM返回为空"
test("LLM基本调用", test_llm_call)

# ============================================
# 5. B-roll提示词生成测试
# ============================================
print("\n" + "="*50)
print("5. B-roll提示词生成测试")
print("="*50)

def test_broll_prompts():
    import importlib.util
    spec = importlib.util.spec_from_file_location('auto_hotvideo', 'auto-hotvideo.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    prompts = module.generate_broll_prompts_from_script(
        "合法性的溢价，是留给后来者的门票。", 
        3, 
        "business"
    )
    print(f"  生成了 {len(prompts)} 个提示词")
    for i, p in enumerate(prompts):
        print(f"  {i+1}. {p[:60]}...")
    assert len(prompts) == 3, f"提示词数量不对: {len(prompts)}"
    # 验证每个提示词都包含风格后缀
    for p in prompts:
        assert "中国人面孔" in p or "Cinematic" in p, f"提示词缺少风格后缀: {p[:50]}"
test("B-roll提示词生成", test_broll_prompts)

# ============================================
# 6. TTS调用测试
# ============================================
print("\n" + "="*50)
print("6. TTS调用测试")
print("="*50)

def test_tts_provider():
    from verticals.tts import get_tts_provider
    provider = get_tts_provider()
    print(f"  TTS提供商: {provider}")
    assert provider == "dashscope", f"TTS提供商应为dashscope: {provider}"
test("TTS提供商", test_tts_provider)

def test_tts_generation():
    from verticals.tts import generate_voiceover
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vo_path = generate_voiceover(
            "测试语音合成",
            Path(tmpdir),
            "zh",
            voice_config={"voice_id": "longanyang"}
        )
        assert vo_path.exists(), f"语音文件不存在: {vo_path}"
        assert vo_path.stat().st_size > 1000, f"语音文件太小: {vo_path.stat().st_size}"
        print(f"  语音文件: {vo_path.name}, 大小: {vo_path.stat().st_size}bytes")
test("TTS语音生成", test_tts_generation)

# ============================================
# 7. 字幕生成测试
# ============================================
print("\n" + "="*50)
print("7. 字幕生成测试")
print("="*50)

def test_captions():
    from verticals.captions import generate_captions
    from verticals.tts import generate_voiceover
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 先生成语音
        vo_path = generate_voiceover(
            "测试字幕生成功能",
            Path(tmpdir),
            "zh"
        )
        # 生成字幕
        result = generate_captions(vo_path, Path(tmpdir), "zh")
        assert result.get("ass_path"), "ASS字幕文件未生成"
        assert result.get("srt_path"), "SRT字幕文件未生成"
        print(f"  ASS: {Path(result['ass_path']).name}")
        print(f"  SRT: {Path(result['srt_path']).name}")
test("字幕生成", test_captions)

# ============================================
# 8. 音乐选择测试
# ============================================
print("\n" + "="*50)
print("8. 音乐选择测试")
print("="*50)

def test_music_selection():
    from verticals.music import select_and_prepare_music, _find_tracks, NICHE_MUSIC_CONFIG
    from verticals.tts import generate_voiceover
    import tempfile
    
    # 验证音乐配置
    print(f"  音乐风格配置: {list(NICHE_MUSIC_CONFIG.keys())}")
    
    for niche in ["general", "viral", "emotion", "business"]:
        tracks = _find_tracks(niche=niche)
        print(f"  {niche}: {len(tracks)}首音乐")
    
    # 测试完整音乐准备
    with tempfile.TemporaryDirectory() as tmpdir:
        vo_path = generate_voiceover("测试", Path(tmpdir), "zh")
        result = select_and_prepare_music(vo_path, Path(tmpdir), niche="business")
        assert result.get("track_path"), "音乐文件未选择"
        assert result.get("duck_filter"), "Duck滤镜未生成"
        print(f"  选中音乐: {Path(result['track_path']).name}")
test("音乐选择", test_music_selection)

# ============================================
# 9. 状态解析测试
# ============================================
print("\n" + "="*50)
print("9. 状态解析测试")
print("="*50)

def test_state_parsing():
    import importlib.util
    spec = importlib.util.spec_from_file_location('state_helper', 'state_helper.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 测试各种输入格式
    test_cases = [
        ("文案：测试文案内容 /图片3 切换2秒", {"image_count": 3, "switch_seconds": 2.0}),
        ("3 切换3秒 图片5 风格:viral", {"image_count": 5, "switch_seconds": 3.0}),
        ("https://test.com/video /图片2", {"image_count": 2}),
        ("画面：情感励志风格", {"niche": "emotion"}),
        ("风格:business", {"niche": "business"}),
    ]
    
    for input_str, expected in test_cases:
        state = module.init_state()
        state = module.parse_user_input(input_str, state)
        for key, value in expected.items():
            actual = state["params"].get(key)
            assert actual == value, f"解析错误: {input_str}, 期望{key}={value}, 实际={actual}"
        print(f"  ✅ '{input_str[:30]}...'")
test("状态解析", test_state_parsing)

# ============================================
# 10. 视频合成测试（模拟）
# ============================================
print("\n" + "="*50)
print("10. 视频合成路径测试")
print("="*50)

def test_output_paths():
    """验证输出路径逻辑"""
    from datetime import datetime
    
    # 模拟输出路径生成
    niches = ["general", "viral", "emotion", "business"]
    date_suffix = datetime.now().strftime("%Y%m%d")
    job_id = "1234567890"
    
    for niche in niches:
        # 素材路径
        asset_path = PROJECT_DIR / "local_assets" / "images" / niche
        assert asset_path.exists(), f"素材目录不存在: {asset_path}"
        
        # 成品视频路径
        output_dir = asset_path / "成品视频"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{niche}_{date_suffix}_{job_id}.mp4"
        print(f"  {niche}: {output_file.relative_to(PROJECT_DIR)}")
test("输出路径验证", test_output_paths)

# ============================================
# 测试结果汇总
# ============================================
print("\n" + "="*50)
print("测试结果汇总")
print("="*50)

print(f"\n✅ 通过: {len(results['passed'])}")
for name in results["passed"]:
    print(f"   - {name}")

if results["failed"]:
    print(f"\n❌ 失败: {len(results['failed'])}")
    for item in results["failed"]:
        print(f"   - {item['name']}: {item['error']}")
    sys.exit(1)
else:
    print("\n🎉 所有测试通过！")
    sys.exit(0)
