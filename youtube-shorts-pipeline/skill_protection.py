#!/usr/bin/env python3
"""
Skill 修改保护机制
禁止修改 skill 文件，除非获得用户文字授权"同意"
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 授权记录文件
AUTHORIZATION_FILE = Path.home() / ".openclaw" / "memory" / "skill-authorization.json"


def request_skill_modification(skill_name: str, reason: str) -> dict:
    """
    请求修改 skill 的授权

    Args:
        skill_name: skill 名称
        reason: 修改原因

    Returns:
        dict: {"authorized": bool, "message": str}
    """
    return {
        "authorized": False,
        "need_authorization": True,
        "message": f"""⚠️ Skill 修改保护

请求修改 skill: {skill_name}
修改原因: {reason}

**安全规则**：
1. 仅接受用户文字输入"同意"
2. 其他任何字符、表情、ID审批一律无效
3. 授权仅一次性生效

请输入"同意"确认修改："""
    }


def verify_authorization(user_input: str, skill_name: str) -> dict:
    """
    验证用户授权

    Args:
        user_input: 用户输入
        skill_name: skill 名称

    Returns:
        dict: {"valid": bool, "message": str}
    """
    # 严格检查：必须是"同意"两个字
    if user_input.strip() != "同意":
        return {
            "valid": False,
            "message": f"❌ 授权无效：必须输入文字\"同意\"，当前输入: \"{user_input}\""
        }

    # 记录授权（一次性）
    AUTHORIZATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    auth_record = {
        "skill_name": skill_name,
        "authorized_at": datetime.now().isoformat(),
        "used": False
    }

    AUTHORIZATION_FILE.write_text(json.dumps(auth_record, ensure_ascii=False, indent=2))

    return {
        "valid": True,
        "message": f"✅ 授权有效：skill \"{skill_name}\" 修改授权已记录（一次性生效）"
    }


def check_and_consume_authorization(skill_name: str) -> bool:
    """
    检查并消费授权（一次性）

    Args:
        skill_name: skill 名称

    Returns:
        bool: 是否已授权
    """
    if not AUTHORIZATION_FILE.exists():
        return False

    try:
        auth_record = json.loads(AUTHORIZATION_FILE.read_text())

        # 检查是否匹配
        if auth_record.get("skill_name") != skill_name:
            return False

        # 检查是否已使用
        if auth_record.get("used", False):
            return False

        # 标记为已使用（一次性）
        auth_record["used"] = True
        auth_record["consumed_at"] = datetime.now().isoformat()
        AUTHORIZATION_FILE.write_text(json.dumps(auth_record, ensure_ascii=False, indent=2))

        return True

    except:
        return False


def protect_skill_file(skill_path: Path) -> bool:
    """
    保护 skill 文件不被修改

    Args:
        skill_path: skill 文件路径

    Returns:
        bool: 是否允许修改
    """
    skill_name = skill_path.stem

    # 检查授权
    if check_and_consume_authorization(skill_name):
        return True

    # 无授权，拒绝修改
    print(f"❌ 拒绝修改 skill: {skill_name}")
    print(f"   原因：未获得用户文字授权\"同意\"")
    print(f"   提示：请先请求授权，用户输入\"同意\"后才能修改")

    return False


if __name__ == "__main__":
    # 测试
    if len(sys.argv) > 1:
        skill_name = sys.argv[1]
        action = sys.argv[2] if len(sys.argv) > 2 else "request"

        if action == "request":
            result = request_skill_modification(skill_name, "测试修改")
            print(result["message"])
        elif action == "verify":
            user_input = sys.argv[3] if len(sys.argv) > 3 else ""
            result = verify_authorization(user_input, skill_name)
            print(result["message"])
        elif action == "check":
            if check_and_consume_authorization(skill_name):
                print(f"✅ {skill_name} 已授权")
            else:
                print(f"❌ {skill_name} 未授权")
    else:
        print("用法: python skill_protection.py <skill_name> [request|verify|check] [user_input]")
