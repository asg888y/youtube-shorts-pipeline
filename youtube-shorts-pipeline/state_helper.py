#!/usr/bin/env python3
"""
auto-hotvideo 状态管理辅助脚本
供OpenClaw读写会话状态
"""

import json
import sys
from pathlib import Path

STATE_FILE = Path.home() / ".openclaw" / "memory" / "auto-hotvideo-state.json"


# 中文风格名称映射
CHINESE_NICHE_MAP = {
    # 情感类
    "情感": "emotion",
    "情感励志": "emotion",
    "情感励志风格": "emotion",
    "温暖": "emotion",
    "治愈": "emotion",
    # 病毒传播类
    "病毒": "viral",
    "病毒传播": "viral",
    "冲击": "viral",
    "震撼": "viral",
    # 知识类
    "知识": "knowledge",
    "科普": "knowledge",
    "专业": "knowledge",
    # 恐怖类
    "恐怖": "horror",
    "悬疑": "horror",
    "惊悚": "horror",
    # 科技类
    "科技": "tech",
    "技术": "tech",
    "未来": "tech",
    # 商业类
    "商业": "business",
    "财富": "business",
    "奢华": "business",
    "商业风格": "business",
    # 通用
    "通用": "general",
    "一般": "general",
}


def _parse_chinese_niche(text: str) -> str | None:
    """解析中文风格名称，返回英文风格代码"""
    text_lower = text.lower()
    for cn_name, en_name in CHINESE_NICHE_MAP.items():
        if cn_name in text_lower:
            return en_name
    return None


def init_state():
    """初始化状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "stage": "hot",
        "topic": None,
        "params": {
            "switch_seconds": 2,
            "image_count": 3,
            "video_count": 0,
            "use_video_api": False,
            "start_with_video": False,
            "use_local": False,      # 新增：是否使用历史素材
            "theme": None,           # 新增：素材主题
            "direct_script": None,   # 新增：直接输入的文案
            "niche": "general"       # 新增：视觉风格
        },
        "hot_topics": [],
        "selected_index": 0,
        "job_id": None,
        "video_path": None,
        "script_source": None       # 新增：文案来源（hot/direct/transcribe）
    }
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    return state


def read_state():
    """读取状态"""
    if not STATE_FILE.exists():
        return init_state()
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def _parse_material_params(params_str: str, state: dict) -> dict:
    """解析素材参数（旧格式，用/分隔）"""
    import re

    # 检查是否有切换秒数（支持小数）
    switch_match = re.search(r'切换(\d+(?:\.\d+)?)秒', params_str)
    if switch_match:
        state["params"]["switch_seconds"] = float(switch_match.group(1))
        params_str = re.sub(r',?\s*切换\d+(?:\.\d+)?秒', '', params_str)

    # 解析素材部分
    parts = params_str.split('/')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if '图片' in part:
            match = re.search(r'图片(\d+)', part)
            if match:
                state["params"]["image_count"] = int(match.group(1))
        elif '视频' in part:
            match = re.search(r'视频(\d+)', part)
            if match:
                state["params"]["video_count"] = int(match.group(1))
                state["params"]["use_video_api"] = True

    return state


def _parse_params_parentheses(params_str: str, state: dict) -> dict:
    """解析括号内的参数（新格式）

    格式：图片3，切换2秒，风格:business
    用逗号或顿号分隔
    """
    import re

    # 用逗号、顿号分隔
    parts = re.split(r'[，,、]', params_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 图片数量
        if '图片' in part:
            match = re.search(r'图片(\d+)', part)
            if match:
                state["params"]["image_count"] = int(match.group(1))

        # 视频数量
        elif '视频' in part:
            match = re.search(r'视频(\d+)', part)
            if match:
                state["params"]["video_count"] = int(match.group(1))
                state["params"]["use_video_api"] = True

        # 切换秒数
        elif '切换' in part:
            match = re.search(r'切换(\d+(?:\.\d+)?)秒?', part)
            if match:
                state["params"]["switch_seconds"] = float(match.group(1))

        # 风格
        elif '风格' in part or 'style' in part.lower():
            match = re.search(r'(?:风格|style)[:：]?\s*(\w+)', part, re.IGNORECASE)
            if match:
                niche = match.group(1).lower()
                valid_niches = ['general', 'viral', 'emotion', 'knowledge', 'horror', 'tech', 'business']
                if niche in valid_niches:
                    state["params"]["niche"] = niche
                    log(f"设置视觉风格: {niche}")
            else:
                # 尝试中文风格名
                niche = _parse_chinese_niche(part)
                if niche:
                    state["params"]["niche"] = niche
                    log(f"设置视觉风格: {niche}")

        # 画面/视觉风格（中文）
        elif '画面' in part or '视觉' in part:
            niche = _parse_chinese_niche(part)
            if niche:
                state["params"]["niche"] = niche
                log(f"设置视觉风格: {niche}")

    return state


def parse_user_input(user_input: str, state: dict) -> dict:
    """解析用户输入，更新状态

    标准格式：
    - 【文案内容】（图片3，切换2秒，风格:business）
    - 【文案...】里面是文案，（）里面是参数
    """
    import re

    # 清理输入
    user_input = user_input.strip()

    # 新格式：【文案...】（参数...）
    # 提取【】内的文案和（）内的参数
    script_match = re.search(r'【(.+?)】', user_input, re.DOTALL)
    params_match = re.search(r'（(.+?)）', user_input)

    if script_match:
        # 提取文案内容
        script_content = script_match.group(1).strip()
        # 移除可能的前缀"文案："
        if script_content.startswith('文案：') or script_content.startswith('文案:'):
            script_content = script_content.split('：' if '：' in script_content else ':', 1)[1].strip()

        state["params"]["direct_script"] = script_content
        state["script_source"] = "direct"
        state["stage"] = "approval"

        # 解析参数
        if params_match:
            params_str = params_match.group(1)
            state = _parse_params_parentheses(params_str, state)

        log(f"直接输入文案: {script_content[:50]}...")
        return state

    # 兼容旧格式：以"文案："开头（无符号标记）
    if user_input.startswith('文案：') or user_input.startswith('文案:') or user_input.lower().startswith('script:'):
        # 提取文案内容
        if user_input.startswith('文案：') or user_input.startswith('文案:'):
            script_content = user_input.split('：' if '：' in user_input else ':', 1)[1].strip()
        else:
            script_content = user_input.split(':', 1)[1].strip()

        # 检查是否包含素材参数
        # 格式：文案：xxx /图片3/视频1,切换2秒
        params_match = re.search(r'(.+?)\s*/(.+)', script_content)
        if params_match:
            script_content = params_match.group(1).strip()
            params_str = '/' + params_match.group(2)
            # 解析素材参数
            state = _parse_material_params(params_str, state)

        state["params"]["direct_script"] = script_content
        state["script_source"] = "direct"
        state["stage"] = "approval"
        log(f"直接输入文案(旧格式): {script_content[:50]}...")
        return state

    # 检查是否是视频链接（需要转录）
    url_match = re.match(r'(https?://[^\s]+)', user_input)
    if url_match:
        url = url_match.group(1)
        remaining = user_input[len(url):].strip()

        state["params"]["direct_script"] = url
        state["script_source"] = "transcribe"
        state["stage"] = "approval"  # 进入审批阶段

        # 解析剩余的素材参数
        if remaining:
            state = _parse_material_params(remaining, state)

        log(f"视频链接，将转录语音: {url}")
        return state

    # 新格式：文案3/视频1,切换2秒
    # 支持：文案X/视频Y/图片Z,切换N秒
    # 支持：视频X,切换N秒
    # 支持：图片X/视频Y,切换N秒

    # 首先检查是否有切换秒数（支持小数）
    switch_match = re.search(r'切换(\d+(?:\.\d+)?)秒', user_input)
    if switch_match:
        state["params"]["switch_seconds"] = float(switch_match.group(1))
        # 移除切换秒数部分，只保留素材部分
        user_input = re.sub(r',?\s*切换\d+(?:\.\d+)?秒', '', user_input)

    # 解析素材部分
    # 格式：文案3/视频1 或 视频1/图片2 等
    parts = user_input.split('/')

    # 重置计数
    state["params"]["image_count"] = 0
    state["params"]["video_count"] = 0
    state["params"]["use_video_api"] = False

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 检查是否是纯数字（热点编号）
        if part.isdigit() and len(parts) == 1:
            idx = int(part) - 1
            if 0 <= idx < len(state.get("hot_topics", [])):
                state["selected_index"] = idx
                state["topic"] = state["hot_topics"][idx]["title"]
                state["script_source"] = "hot"
            continue

        # 解析素材类型和数量
        if '文案' in part:
            # 文案数量，主要用于计算总素材数
            match = re.search(r'文案(\d+)', part)
            if match:
                # 文案本身不生成素材，但影响总素材数
                pass
        elif '图片' in part:
            match = re.search(r'图片(\d+)', part)
            if match:
                state["params"]["image_count"] = int(match.group(1))
        elif '视频' in part:
            match = re.search(r'视频(\d+)', part)
            if match:
                state["params"]["video_count"] = int(match.group(1))
                state["params"]["use_video_api"] = True
        elif '开头视频' in part:
            state["params"]["start_with_video"] = True
        elif '历史素材' in part:
            state["params"]["use_local"] = True
            # 提取主题
            theme_match = re.search(r'历史素材\s*[:：]?\s*(\w+)', part)
            if theme_match:
                state["params"]["theme"] = theme_match.group(1)
        elif '画面' in part or '视觉' in part:
            # 解析中文风格名称：画面：情感励志风格 → emotion
            niche = _parse_chinese_niche(part)
            if niche:
                state["params"]["niche"] = niche
                log(f"设置视觉风格: {niche}")
        elif '风格' in part or 'style' in part.lower():
            # 解析风格参数：风格:viral 或 style:viral
            match = re.search(r'(?:风格|style)[:：]?\s*(\w+)', part, re.IGNORECASE)
            if match:
                niche = match.group(1).lower()
                # 验证风格是否存在
                valid_niches = ['general', 'viral', 'emotion', 'knowledge', 'horror', 'tech', 'business']
                if niche in valid_niches:
                    state["params"]["niche"] = niche
                    log(f"设置视觉风格: {niche}")
        else:
            # 如果不是素材格式，可能是自定义主题
            if not state["topic"]:
                state["topic"] = part
                state["script_source"] = "hot"

    # 如果没有设置切换秒数，使用默认值
    if "switch_seconds" not in state["params"] or state["params"]["switch_seconds"] <= 0:
        state["params"]["switch_seconds"] = 2.0

    return state


def log(msg: str):
    """简单日志输出"""
    print(f"  {msg}")


def main():
    if len(sys.argv) < 2:
        print("用法: python state_helper.py [init|read|save|parse] [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        state = init_state()
        print(json.dumps(state, ensure_ascii=False))

    elif cmd == "read":
        state = read_state()
        print(json.dumps(state, ensure_ascii=False))

    elif cmd == "save":
        if len(sys.argv) < 3:
            print("用法: python state_helper.py save '{json}'")
            sys.exit(1)
        state = json.loads(sys.argv[2])
        save_state(state)
        print("OK")

    elif cmd == "parse":
        if len(sys.argv) < 3:
            print("用法: python state_helper.py parse '用户输入'")
            sys.exit(1)
        state = read_state()
        user_input = sys.argv[2]
        state = parse_user_input(user_input, state)
        state["stage"] = "generate"
        save_state(state)
        print(json.dumps(state, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
