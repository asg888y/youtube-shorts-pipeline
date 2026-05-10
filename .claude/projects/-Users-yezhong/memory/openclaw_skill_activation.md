# OpenClaw Skill 多轮对话管理指南

## Skill 激活机制

### 触发词类型

| 触发词 | 作用 | 适用场景 |
|--------|------|----------|
| 热点视频 | 首次激活/重新开始 | 新任务、状态异常 |
| 继续生成视频 | 恢复任务 | 任务中断、需要提醒 |
| 执行视频生成 | 执行当前阶段 | 明确执行指令 |

### 状态持久化

**状态文件**：`~/.openclaw/memory/auto-hotvideo-state.json`

**状态字段**：
```json
{
    "stage": "hot/approval/generate/completed",
    "topic": "主题",
    "params": {
        "switch_seconds": 2,
        "image_count": 3,
        "direct_script": "文案内容"
    },
    "script_source": "hot/direct/transcribe",
    "job_id": "任务ID",
    "video_path": "视频路径"
}
```

### 阶段流程

```
hot（获取热点）
  ↓
approval（成本审批）
  ↓
generate（生成视频）
  ↓
completed（完成）
```

## 多轮对话处理

### 场景1：正常流程（无需重新激活）

**示例**：
```
第1轮：用户输入"热点视频"
  → OpenClaw 获取热点列表
  → 状态：stage="hot"

第2轮：用户输入"3 /图片5"
  → OpenClaw 解析参数
  → 状态：stage="approval"

第3轮：用户输入"同意"
  → OpenClaw 执行生成
  → 状态：stage="generate"

第4轮：用户询问进度
  → OpenClaw 查看状态文件
  → 继续执行或报告进度
```

**结论**：状态持久化，无需重新激活

### 场景2：任务中断（使用恢复触发词）

**示例**：
```
第1-3轮：正常流程
  → 状态：stage="generate"

中断：用户离开，OpenClaw 会话结束

第4轮（新会话）：用户输入"继续生成视频"
  → OpenClaw 检查状态文件
  → 发现未完成任务
  → 恢复执行
```

**结论**：使用"继续生成视频"恢复

### 场景3：状态异常（重新激活）

**示例**：
```
状态文件损坏或逻辑错误

用户输入"热点视频"
  → OpenClaw 初始化状态
  → 重新开始
```

**结论**：重新激活会清空状态

## 最佳实践

### ✅ 推荐做法

1. **正常流程**：直接输入下一步指令
   - 无需触发词
   - OpenClaw 自动读取状态

2. **任务中断**：使用"继续生成视频"
   - 提醒 OpenClaw 检查状态
   - 自动恢复

3. **查看状态**：询问"当前进度"
   - OpenClaw 查看状态文件
   - 报告当前阶段

### ❌ 避免做法

1. **每轮都触发**：
   - 不需要每次输入"热点视频"
   - 会重新初始化，丢失进度

2. **忽略状态**：
   - 不要假设 OpenClaw 会记住
   - 状态文件是唯一持久化

3. **跨会话不检查**：
   - 新会话开始时检查状态
   - 使用恢复触发词

## 状态检查命令

### 手动检查

```bash
# 查看状态文件
cat ~/.openclaw/memory/auto-hotvideo-state.json | python3 -m json.tool

# 查看任务进度
cd /Users/yezhong/youtube-shorts-pipeline
python3 auto-hotvideo.py status

# 查看未完成任务
python3 auto-hotvideo.py status
```

### OpenClaw 检查

**询问 OpenClaw**：
- "当前任务进度"
- "查看状态文件"
- "继续生成视频"

## 常见问题

### Q1: 多轮对话后，OpenClaw 还记得吗？

**A**: 是的，状态保存在文件中：
- 状态文件：`~/.openclaw/memory/auto-hotvideo-state.json`
- OpenClaw 每次都会读取
- 跨会话也能恢复

### Q2: 什么时候需要重新激活？

**A**: 仅在以下情况：
- 状态文件损坏
- 需要重新开始
- 想放弃当前任务

### Q3: 如何确认当前状态？

**A**: 三种方式：
1. 询问 OpenClaw："当前进度"
2. 手动查看状态文件
3. 使用命令：`python3 auto-hotvideo.py status`

### Q4: 任务中断后如何恢复？

**A**: 使用恢复触发词：
- "继续生成视频"
- 或询问："恢复上次任务"

## 总结

| 场景 | 操作 | 是否重新激活 |
|------|------|--------------|
| 正常流程 | 直接输入下一步 | ❌ 不需要 |
| 任务中断 | "继续生成视频" | ❌ 不需要 |
| 状态异常 | "热点视频" | ✅ 需要 |
| 查看进度 | 询问状态 | ❌ 不需要 |

**核心原则**：
- 状态持久化，无需每次激活
- 使用恢复触发词继续任务
- 仅在异常时重新激活