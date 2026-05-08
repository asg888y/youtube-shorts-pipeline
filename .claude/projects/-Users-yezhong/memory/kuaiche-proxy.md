---
name: 快车VPN代理配置
description: 快车VPN代理配置信息，按需调用
type: reference
originSessionId: 86918430-225d-42b4-a268-5cd6f2a959b9
---

# 快车VPN代理配置

## 基本信息
- 应用：快车.app (com.wjkc.soft)
- 配置路径：`~/Library/Application Support/com.wjkc.soft/config.json`
- mixed-port: 7890 (HTTP/SOCKS5混合端口)
- external-controller: 127.0.0.1:9090 (RESTful API，需启用)

## 使用方式

### 临时使用代理（推荐）
```bash
# 单次命令使用代理
curl -x http://127.0.0.1:7890 https://github.com

# git使用代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 用完后关闭代理
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 启动/停止快车
```bash
# 启动
open -a "快车"

# 停止
killall "快车"
```

### 检查代理状态
```bash
curl -x http://127.0.0.1:7890 -s https://www.google.com -o /dev/null -w "%{http_code}"
# 返回200表示代理正常
```

### 切换模式
```bash
# global模式（所有流量走代理）
python3 -c "import json; c=json.load(open('$HOME/Library/Application Support/com.wjkc.soft/config.json')); c['mode']='global'; json.dump(c, open('$HOME/Library/Application Support/com.wjkc.soft/config.json','w'), indent=2)"

# rule模式（国外网站走代理，国内直连）
python3 -c "import json; c=json.load(open('$HOME/Library/Application Support/com.wjkc.soft/config.json')); c['mode']='rule'; json.dump(c, open('$HOME/Library/Application Support/com.wjkc.soft/config.json','w'), indent=2)"
```

## ⚠️ 重要：快车需要手动点击"开启"按钮

快车是 Flutter GUI 应用，**无法通过命令行直接开启代理**。

### 解决方案

1. **手动操作**：在快车界面点击"开启"按钮
2. **external-controller API**（需先在快车中开启一次代理后才能使用）

### 启用 external-controller

```bash
# 修改配置文件启用API
python3 -c "
import json
config_path = '$HOME/Library/Application Support/com.wjkc.soft/config.json'
with open(config_path.replace('\$HOME', '$HOME'), 'r') as f:
    config = json.load(f)
config['external-controller'] = '127.0.0.1:9090'
with open(config_path.replace('\$HOME', '$HOME'), 'w') as f:
    json.dump(config, f, indent=2)
"
# 重启快车后生效
```

### 通过 API 控制代理（需先启用 external-controller）

```bash
# 检查状态
curl http://127.0.0.1:9090/proxies

# 切换代理模式
curl -X PUT http://127.0.0.1:9090/configs -d '{"mode":"global"}'
```

## 注意事项
- **不要影响全局**：其他业务需要国内网络
- **Claude会话用国内网络**：不要全局开启代理
- **按需使用**：只在访问国外网站时临时启用代理
- 重启快车后需要等待几秒让代理启动
- **快车需要手动点击开启**：这是目前的限制
