---
name: container resource limits mandatory
description: 服务器部署任何Docker容器必须设资源上限
type: feedback
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---

## 铁律

**部署或重建任何 Docker 容器时，必须立即设置资源限制。**
禁止未设限的容器在服务器上运行。

## 规则

- 所有新增部署的容器，内存上限 ≤ 1GB
- 部署后立即设限，不允许无限制运行

## 当前限制 (8.138.165.244, 2c4g)

| 容器 | 内存上限 | Swap | CPU |
|------|---------|------|-----|
| umi-ocr | 1GB | 1.5GB | 2 |
| YXiao-old | 1GB | 1.5GB | 2 |
| n8n | 500MB | 750MB | - |
| www | 500MB | 1GB | 1 |

## 检查命令

```bash
docker inspect <container> --format 'Memory: {{.HostConfig.Memory}} Swap: {{.HostConfig.MemorySwap}} CPUs: {{.HostConfig.NanoCpus}}'
```

## Why

2c4g 服务器跑 5 个容器，任一容器 OOM 或 CPU 吃满都会导致整个系统无响应。Umi-OCR 加载 PaddleOCR 模型时需要限制，否则可能触发宿主机 OOM。
