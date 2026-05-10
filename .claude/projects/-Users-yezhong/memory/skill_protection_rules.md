---
name: Skill修改保护机制
description: 禁止修改skill文件，除非获得用户文字授权"同意"
type: feedback
originSessionId: a425339a-241d-4248-bd18-46b4039d93b8
---
## Skill 修改保护规则

**强制规则**：所有 skill 文件受保护，禁止修改！

### 授权要求

1. **唯一有效授权**：用户文字输入"同意"
2. **无效授权**：
   - 任何其他字符（"好的"、"OK"、"可以"等）
   - 表情符号（👍、✅等）
   - ID审批（数字、UUID等）
3. **一次性生效**：授权用后即废，需重新授权

### 实现机制

**保护脚本**：`skill_protection.py`

**核心函数**：
- `request_skill_modification()`: 请求修改授权
- `verify_authorization()`: 验证用户授权
- `check_and_consume_authorization()`: 检查并消费授权（一次性）

**授权记录**：`~/.openclaw/memory/skill-authorization.json`

### 使用流程

```
1. AI 请求修改 skill
2. 系统提示用户输入"同意"
3. 用户输入"同意"
4. 系统验证并记录授权
5. AI 修改 skill（一次性）
6. 授权自动失效
```

### Why

防止 AI 未经授权修改 skill 文件，确保用户对工具行为有完全控制权。避免意外修改导致功能异常或安全问题。

### How to apply

修改任何 skill 文件前，必须：
1. 调用 `skill_protection.py` 请求授权
2. 等待用户输入"同意"
3. 验证授权通过后才能修改
