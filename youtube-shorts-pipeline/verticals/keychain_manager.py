"""密钥管理 - 使用 macOS Keychain 安全存储 API 密钥"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

# 密钥链服务名称
KEYCHAIN_SERVICE = "verticals-api-keys"

# 非敏感配置文件路径（只存储非敏感设置）
CONFIG_FILE = Path.home() / ".verticals" / "config.json"

# 敏感密钥列表（存储在 Keychain）
SENSITIVE_KEYS = [
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ELEVENLABS_API_KEY",
    "PEXELS_API_KEY",
    "MINIMAX_API_KEY",
    "RUNNINGHUB_API_KEY",
    "DASHSCOPE_API_KEY",
    "XUNFEI_API_KEY",
    "NEWSAPI_KEY",
]


def _get_from_keychain(key_name: str) -> Optional[str]:
    """从 macOS Keychain 获取密钥"""
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", key_name,
                "-w"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _save_to_keychain(key_name: str, key_value: str) -> bool:
    """将密钥保存到 macOS Keychain"""
    try:
        # 先删除旧的（如果存在）
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", key_name
            ],
            capture_output=True,
            timeout=5
        )

        # 添加新的
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", key_name,
                "-w", key_value,
                "-U"  # 允许更新
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"保存密钥失败: {e}")
        return False


def _delete_from_keychain(key_name: str) -> bool:
    """从 macOS Keychain 删除密钥"""
    try:
        result = subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-s", KEYCHAIN_SERVICE,
                "-a", key_name
            ],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0 or "The specified item could not be found" in result.stderr
    except Exception:
        return False


def get_key(key_name: str) -> str:
    """获取 API 密钥（优先级：环境变量 > Keychain > config.json）"""
    import os

    # 1. 首先检查环境变量
    env_val = os.environ.get(key_name)
    if env_val:
        return env_val

    # 2. 如果是敏感密钥，从 Keychain 获取
    if key_name in SENSITIVE_KEYS:
        keychain_val = _get_from_keychain(key_name)
        if keychain_val:
            return keychain_val

    # 3. 最后从 config.json 获取（非敏感配置）
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            val = cfg.get(key_name)
            if val:
                return val
        except Exception:
            pass

    return ""


def set_key(key_name: str, key_value: str) -> bool:
    """设置 API 密钥（敏感密钥存 Keychain，非敏感存 config.json）"""
    if key_name in SENSITIVE_KEYS:
        # 敏感密钥存 Keychain
        return _save_to_keychain(key_name, key_value)
    else:
        # 非敏感配置存 config.json
        cfg = {}
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
            except Exception:
                pass
        cfg[key_name] = key_value
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
        return True


def delete_key(key_name: str) -> bool:
    """删除 API 密钥"""
    if key_name in SENSITIVE_KEYS:
        return _delete_from_keychain(key_name)
    else:
        cfg = {}
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                if key_name in cfg:
                    del cfg[key_name]
                    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
            except Exception:
                pass
        return True


def migrate_to_keychain() -> dict:
    """将 config.json 中的敏感密钥迁移到 Keychain"""
    migrated = {}

    if not CONFIG_FILE.exists():
        return migrated

    try:
        cfg = json.loads(CONFIG_FILE.read_text())

        for key_name in SENSITIVE_KEYS:
            if key_name in cfg and cfg[key_name]:
                key_value = cfg[key_name]
                if _save_to_keychain(key_name, key_value):
                    migrated[key_name] = "已迁移到 Keychain"
                    # 从 config.json 删除
                    del cfg[key_name]
                else:
                    migrated[key_name] = "迁移失败"

        # 保存更新后的 config.json（只保留非敏感配置）
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

    except Exception as e:
        migrated["error"] = str(e)

    return migrated


def list_keys() -> dict:
    """列出所有已存储的密钥（不显示值）"""
    import os

    result = {}

    for key_name in SENSITIVE_KEYS:
        # 检查环境变量
        if os.environ.get(key_name):
            result[key_name] = "环境变量"
        # 检查 Keychain
        elif _get_from_keychain(key_name):
            result[key_name] = "Keychain"
        # 检查 config.json
        elif CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text())
                if cfg.get(key_name):
                    result[key_name] = "config.json（建议迁移）"
            except Exception:
                pass

    return result


def load_config() -> dict:
    """加载配置（敏感密钥从 Keychain 获取，非敏感从 config.json）"""
    cfg = {}

    # 加载非敏感配置
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass

    # 加载敏感密钥（从 Keychain）
    for key_name in SENSITIVE_KEYS:
        key_value = get_key(key_name)
        if key_value:
            cfg[key_name] = key_value

    return cfg


def setup_keys_interactive():
    """交互式密钥设置"""
    print("=" * 60)
    print("API 密钥设置（使用 macOS Keychain 安全存储）")
    print("=" * 60)
    print()

    # 先迁移现有密钥
    print("检查现有密钥...")
    migrated = migrate_to_keychain()
    if migrated:
        print("已迁移密钥:")
        for k, v in migrated.items():
            if v != "迁移失败":
                print(f"  ✓ {k}: {v}")
        print()

    # 显示当前状态
    current = list_keys()
    print("当前密钥状态:")
    for k, v in current.items():
        print(f"  {k}: {v}")
    print()

    # 交互设置
    print("请输入需要设置的密钥（输入密钥名称和值，用空格分隔）")
    print("例如：DASHSCOPE_API_KEY sk-xxxxx")
    print("输入 'q' 退出")
    print()

    while True:
        try:
            input_str = input("> ").strip()
            if input_str.lower() == 'q':
                break

            parts = input_str.split(maxsplit=1)
            if len(parts) != 2:
                print("格式错误，请输入：密钥名称 密钥值")
                continue

            key_name, key_value = parts
            if key_name not in SENSITIVE_KEYS:
                print(f"警告：{key_name} 不是敏感密钥，将存储在 config.json")

            if set_key(key_name, key_value):
                print(f"✓ {key_name} 已保存")
            else:
                print(f"✗ {key_name} 保存失败")

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print()
    print("密钥设置完成")
    print("敏感密钥已安全存储在 macOS Keychain")
    print("非敏感配置存储在 ~/.verticals/config.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python keychain_manager.py migrate   - 迁移现有密钥到 Keychain")
        print("  python keychain_manager.py list       - 列出密钥状态")
        print("  python keychain_manager.py setup      - 交互式设置")
        print("  python keychain_manager.py get KEY    - 获取密钥值")
        print("  python keychain_manager.py set KEY VAL - 设置密钥")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "migrate":
        result = migrate_to_keychain()
        print("迁移结果:")
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif cmd == "list":
        result = list_keys()
        print("密钥状态:")
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif cmd == "setup":
        setup_keys_interactive()

    elif cmd == "get":
        if len(sys.argv) < 3:
            print("请指定密钥名称")
            sys.exit(1)
        key_name = sys.argv[2]
        value = get_key(key_name)
        if value:
            print(value)
        else:
            print("密钥不存在")

    elif cmd == "set":
        if len(sys.argv) < 4:
            print("请指定密钥名称和值")
            sys.exit(1)
        key_name = sys.argv[2]
        key_value = sys.argv[3]
        if set_key(key_name, key_value):
            print("✓ 密钥已保存")
        else:
            print("✗ 保存失败")

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)