---
name: 问题解决执行标准
description: ⭐ 解决任何问题的标准流程：诊断→定位→修复→验证→固化
type: feedback
originSessionId: 47c54732-dd45-463b-83fa-e4205eb4dac9
---
# 问题解决执行标准

## 核心原则

**任何问题的本质都是修复系统/管线，不是做一次性修复。**

## 标准执行流程

### 1. 诊断阶段
- 读取相关日志文件，定位错误模式
- 对照已知问题清单匹配错误特征
- 输出格式：【问题】→【根因】→【修复方案】→【验证步骤】

### 2. 定位阶段
- 沿调用链路逐层排查：配置→入口→模块→函数
- 检查关键文件：MEMORY.md、DEPENDENCIES.md、配置文件
- 确认问题范围：单点故障 vs 系统性问题

### 3. 修复阶段
- **禁止反复试错**：最多尝试2次，失败即跳过使用fallback
- **一步到位**：修改时检查所有关联文件（参考hotvideo_config_flow.md）
- **保持兼容**：新增功能不破坏现有流程
- **配置变更必须验证**：修改任何配置文件后，立即验证基本功能是否正常

### 4. 遍历验证阶段（必须）

**遍历验证**：覆盖所有错误可能性，验证所有逻辑关系都能正常调用。

#### 验证要求
- **必须遍历所有分支**：正常流程、边界条件、错误处理、fallback机制
- **必须验证调用链路**：从入口到出口的完整路径
- **必须覆盖所有风格**：general/viral/emotion/knowledge/horror/tech/business
- **必须测试API失败场景**：模拟超时、空响应、格式错误

#### 遍历验证清单
```python
# 遍历验证必须包含以下测试类
tests = [
    # 0. 配置变更验证（修复后立即执行）
    ("配置变更-基本功能", test_config_change_basic),
    ("配置变更-工具可用性", test_config_change_tools),
    ("配置变更-服务重启", test_config_change_restart),

    # 1. 配置层遍历
    ("配置加载-默认", test_config_default),
    ("配置加载-所有风格", test_config_all_niches),

    # 2. 解析层遍历
    ("风格解析-中文", test_niche_chinese),
    ("风格解析-英文", test_niche_english),
    ("风格解析-别名", test_niche_aliases),
    ("风格解析-无效值", test_niche_invalid),

    # 3. 生成层遍历
    ("文案生成-正常", test_draft_normal),
    ("文案生成-空输入", test_draft_empty),
    ("文案生成-超长输入", test_draft_long),
    ("图片生成-API成功", test_broll_api_success),
    ("图片生成-API失败-fallback", test_broll_api_fallback),
    ("图片生成-本地素材", test_broll_local),

    # 4. 合成层遍历
    ("语音合成-所有音色", test_tts_all_voices),
    ("字幕生成-样式匹配", test_captions_style),
    ("音乐选择-风格匹配", test_music_niche_match),
    ("视频合成-完整流程", test_assemble_full),

    # 5. 错误处理遍历
    ("API超时处理", test_api_timeout),
    ("API空响应处理", test_api_empty),
    ("API格式错误处理", test_api_invalid_format),
    ("素材不足处理", test_material_shortage),
    ("音频截断逻辑", test_audio_truncate),
]
```

#### 验证输出格式
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

#### 验证通过标准
- 通过率 ≥ 90%
- 失败的测试必须有明确的fallback机制
- 所有关键路径必须100%通过

### 5. 固化阶段
- 将解决方案保存为记忆文件
- 更新相关文档（README.md、DEPENDENCIES.md）
- 同步修改关联配置
- **GitHub同步迭代**：提交代码变更，推送至远程仓库

### 6. GitHub同步（必须）

**每次修复和维护必须同步到GitHub。**

#### 同步流程
```bash
# 1. 检查变更
git status
git diff

# 2. 提交变更
git add -A
git commit -m "fix: 问题描述 #issue编号"

# 3. 推送到远程
git push origin main
```

#### 提交信息规范
- `fix:` 修复bug
- `feat:` 新功能
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试相关

#### 禁止事项
- 禁止跳过git提交
- 禁止使用无意义的commit message
- 禁止忘记push到远程

## 热点视频项目修改清单

| 修改目标 | 需要同步修改的文件 |
|----------|-------------------|
| 新增风格 | niches/{name}.yaml + music.py NICHE_MUSIC_CONFIG + state_helper.py CHINESE_NICHE_MAP + valid_niches |
| 修改文案框架 | bd-wenan/SKILL.md（draft.py会自动读取） |
| 修改场景模式 | niches/{name}.yaml 的 scene_modes + niche.py 的读取函数 |
| 修改字幕样式 | niches/{name}.yaml 的 captions 部分 |
| 修改音乐 | music/{niche}/ 目录 + music.py NICHE_MUSIC_CONFIG |
| 修改素材命名 | broll.py generate_broll() + auto-hotvideo.py _assemble_mixed() |

## 测试验证标准

### 遍历验证定义

**遍历验证** = 覆盖所有错误可能性 + 验证所有逻辑关系都能正常调用

### 测试脚本结构
```python
# test_pipeline.py
tests = [
    ("配置加载", test_config),
    ("风格解析", test_niche_parsing),
    ("文案生成", test_draft_generation),
    ("图片生成", test_broll_generation),
    ("语音合成", test_tts),
    ("字幕生成", test_captions),
    ("音乐选择", test_music),
    ("视频合成", test_assemble),
    ("完整流程", test_full_pipeline),
    ("错误处理", test_error_handling),
]
```

### 测试输出格式
```
✅ 测试名称 - 通过 (耗时: Xs)
❌ 测试名称 - 失败: 错误信息
⏭️ 测试名称 - 跳过: 原因
```

## 禁止事项

1. **禁止反复调试**：同一问题最多尝试2次
2. **禁止未审批替换方案**：必须100%按用户要求执行
3. **禁止跳过遍历验证**：任何修改必须跑遍历验证，覆盖所有分支
4. **禁止忘记固化**：解决问题后必须保存记忆
5. **禁止部分验证**：验证必须遍历所有风格、所有分支、所有错误场景
6. **禁止跳过GitHub同步**：每次修复和维护必须提交代码并推送到远程仓库
7. **禁止配置变更不验证**：修改任何配置后必须立即验证基本功能，否则就是制造问题

## Why

用户意图永远是长期系统改进，不是临时修复。每次解决问题都要留下可复用的知识。

## How to apply

遇到任何问题时：
1. 先读记忆（MEMORY.md + 相关记忆文件）
2. 按标准流程执行
3. 解决后保存新记忆
