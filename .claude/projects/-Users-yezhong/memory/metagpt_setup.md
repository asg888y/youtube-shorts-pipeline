---
name: MetaGPT Setup
description: MetaGPT安装配置，讯飞API，使用方法
type: reference
originSessionId: 8120d216-8261-4c2e-97b7-954d2fb023d0
---
## MetaGPT 配置

**安装位置**: conda 环境 `metagpt`

**讯飞 API 配置** (`~/.metagpt/config2.yaml`):
```yaml
llm:
  api_type: "openai"
  model: "astron-code-latest"
  base_url: "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2"
  api_key: "a5931cb8f8ece241f7b7ec17bcb8c8e7:NWQ5ZDNjZTUxYWYyZTE3OGJkYzRhOGYx"
```

**使用方法**:
```bash
# 终端直接运行
metagpt "创建一个计算器程序"

# 生成的项目位置
~/workspace/
```

**讯飞 API 端点**:
- OpenAI 兼容: `https://maas-coding-api.cn-huabei-1.xf-yun.com/v2`
- Anthropic 兼容: `https://maas-coding-api.cn-huabei-1.xf-yun.com/anthropic`
- 模型: `astron-code-latest`

**Conda 环境**:
```bash
conda activate metagpt
```
