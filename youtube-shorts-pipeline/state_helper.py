#!/usr/bin/env python3
"""
auto-hotvideo 状态管理辅助脚本
供OpenClaw读写会话状态
"""

import json
import sys
from pathlib import Path

STATE_FILE = Path.home() / ".openclaw" / "memory" / "auto-hotvideo-state.json"


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
            "start_with_video": False
        },
        "hot_topics": [],
        "selected_index": 0,
        "job_id": None,
        "video_path": None
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


def parse_user_input(user_input: str, state: dict) -> dict:
    """解析用户输入，更新状态"""
    import re

    parts = user_input.strip().split()

    for part in parts:
        # 纯数字 = 选择热点编号
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(state.get("hot_topics", [])):
                state["selected_index"] = idx
                state["topic"] = state["hot_topics"][idx]["title"]

        # 切换X秒
        elif match := re.match(r"切换(\d+)秒", part):
            state["params"]["switch_seconds"] = int(match.group(1))

        # 图片X
        elif match := re.match(r"图片(\d+)", part):
            state["params"]["image_count"] = int(match.group(1))

        # 视频X
        elif match := re.match(r"视频(\d+)", part):
            state["params"]["video_count"] = int(match.group(1))
            state["params"]["use_video_api"] = True

        # 开头视频
        elif part == "开头视频":
            state["params"]["start_with_video"] = True

        # 其他 = 自定义主题
        elif not part.startswith("切换") and not part.startswith("图片"):
            if not state["topic"]:
                state["topic"] = user_input.strip()
                break

    return state


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
