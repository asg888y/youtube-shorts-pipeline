---
name: 问题解决执行标准
description: ⭐ 解决任何问题的标准流程：六阶段强制执行，禁止跳过任何阶段
type: feedback
originSessionId: 47c54732-dd45-463b-83fa-e4205eb4dac9
---
# 问题解决执行标准

## 核心原则

**任何问题的本质都是修复系统/管线，不是做一次性修复。**

---

## 标准执行作业流程（六阶段）

### 阶段一：操作前强制检查

```bash
1. 读取相关记忆文件（MEMORY.md + 项目记忆）
2. 读取DEPENDENCIES.md（如存在）
3. 确认当前工作目录和git状态
```

### 阶段二：修改阶段

```bash
1. 明确修改目标和范围
2. 列出所有需要修改的文件清单
3. 逐个修改，记录每个变更
```

### 阶段三：配置变更特殊处理

```bash
1. 修改配置前：记录原值
2. 修改配置后：立即验证基本功能
3. 验证项目：
   - 服务能否正常启动
   - 核心工具是否可用（exec/read/write等）
   - 基本命令能否执行
4. 验证失败：立即回滚
```

### 阶段四：遍历验证阶段

```bash
1. 编写/运行测试脚本
2. 覆盖范围：
   - 配置变更验证（修改配置后必须执行）
   - 正常流程验证
   - 边界条件验证
   - 错误处理验证
   - 所有风格/分支验证
3. 输出验证报告
4. 通过率要求：≥90%，关键路径100%
```

### 阶段五：固化阶段

```bash
1. 更新记忆文件（如需要）
2. 更新文档（README.md、DEPENDENCIES.md）
```

### 阶段六：GitHub同步阶段

```bash
1. git status 确认变更
2. git add 相关文件
3. git commit 规范提交信息
4. git push 推送到远程
5. 确认推送成功
```

---

## 禁止事项

1. **禁止修改配置后不验证**：任何配置变更必须立即验证基本功能
2. **禁止跳过遍历验证**：任何修改必须跑遍历验证，覆盖所有分支
3. **禁止忘记GitHub同步**：每次修复和维护必须提交代码并推送到远程仓库
4. **禁止自己制造问题自己发现不了**：修改后必须验证后果
5. **禁止部分验证**：验证必须遍历所有风格、所有分支、所有错误场景

---

## 遍历验证清单

```python
tests = [
    # 阶段四-1: 配置变更验证（修改配置后必须执行）
    ("配置变更-服务启动", test_config_service_start),
    ("配置变更-工具可用性", test_config_tools_available),
    ("配置变更-基本命令", test_config_basic_commands),

    # 阶段四-2: 配置层遍历
    ("配置加载-默认", test_config_default),
    ("配置加载-所有风格", test_config_all_niches),

    # 阶段四-3: 解析层遍历
    ("风格解析-中文", test_niche_chinese),
    ("风格解析-英文", test_niche_english),
    ("风格解析-别名", test_niche_aliases),
    ("风格解析-无效值", test_niche_invalid),

    # 阶段四-4: 生成层遍历
    ("文案生成-正常", test_draft_normal),
    ("文案生成-空输入", test_draft_empty),
    ("文案生成-超长输入", test_draft_long),
    ("图片生成-API成功", test_broll_api_success),
    ("图片生成-API失败-fallback", test_broll_api_fallback),
    ("图片生成-本地素材", test_broll_local),

    # 阶段四-5: 合成层遍历
    ("语音合成-所有音色", test_tts_all_voices),
    ("字幕生成-样式匹配", test_captions_style),
    ("音乐选择-风格匹配", test_music_niche_match),
    ("视频合成-完整流程", test_assemble_full),

    # 阶段四-6: 错误处理遍历
    ("API超时处理", test_api_timeout),
    ("API空响应处理", test_api_empty),
    ("API格式错误处理", test_api_invalid_format),
    ("素材不足处理", test_material_shortage),
    ("音频截断逻辑", test_audio_truncate),
]
```

---

## 验证输出格式

```
========== 遍历验证报告 ==========
总计: X 个测试
✅ 通过: Y 个
❌ 失败: Z 个
⏭️ 跳过: W 个

失败详情:
- test_xxx: 错误信息
- test_yyy: 错误信息

覆盖率: XX%
==================================
```

---

## Why

用户意图永远是长期系统改进，不是临时修复。每次解决问题都要留下可复用的知识。

## How to apply

遇到任何问题时：
1. 按六阶段流程执行
2. 每个阶段必须完成才能进入下一阶段
3. 解决后保存新记忆
