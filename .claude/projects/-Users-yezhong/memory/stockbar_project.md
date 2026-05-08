---
name: StockBar项目
description: macOS状态栏股票期货行情显示器
type: project
originSessionId: 2ee3386f-9e0e-4167-ad4b-49dfb8d3f63b
---
## 项目概述
macOS原生状态栏应用，实时显示股票/期货行情，支持轮播显示。

## 位置
`~/stockbar-app/`

## 主要文件
- `main.swift` - Swift源码，编译后运行
- `stockbar-cli.py` - 命令行管理工具（可选）
- `config.json` - 中文配置文件，直接编辑即可

## 使用方法

### 启动
```bash
~/stockbar-app/stockbar &
```

### 停止
点击状态栏图标 -> 退出，或 `pkill -f stockbar`

### 配置
直接编辑 `~/stockbar-app/config.json`：
```json
{
  "刷新间隔_秒": 10,
  "显示起始位置_从1开始": 1,
  "显示数量_0表示全部": 0,
  "品种列表": [
    { "代码": "600519", "名称": "贵州茅台" },
    { "代码": "RB2610", "名称": "螺纹钢2610" }
  ]
}
```

### 重新编译
```bash
cd ~/stockbar-app && swiftc -o stockbar main.swift -framework Cocoa
```

## 支持的品种
- 股票：上交所(6开头)、深交所(0/3开头)
- 期货：中金所(IF/IC/IH/IM)、上期所(RB/HC/AU/AG/CU等)、郑商所(FG/MA/TA等)、大商所(I/J/JM等)

## 数据源
东方财富API（免费）：`http://push2.eastmoney.com/api/qt/stock/get`

## GitHub仓库
https://github.com/asg888y/stockbar

## 注意事项
- 配置文件保存后自动生效（2秒内）
- 状态栏每3秒轮播下一个品种
- 显示涨跌幅百分比
- 用MarkEdit打开配置文件编辑
