# 🚀 Freqtrade 快速启动指南

## 📋 当前配置状态

✅ **动态币对系统已配置**（符合NostalgiaForInfinity原作者推荐）
- 自动筛选 ~73 个优质币对
- 每30分钟自动更新
- 7层过滤器（黑名单+年龄+价格+价差+波动率）

---

## 🎯 场景1：实盘交易

### 方法1：只启动Bot（推荐，简单稳定）

```bash
./start_bot_only.sh
```

**优点：**
- ✅ 简单可靠，不会有FreqUI端口冲突
- ✅ 使用API查看状态
- ✅ 更适合服务器后台运行

**查看Bot状态：**
```bash
# 查看交易状态
curl http://127.0.0.1:8082/api/v1/status | python3 -m json.tool

# 查看当前币对
curl http://127.0.0.1:8082/api/v1/whitelist | python3 -m json.tool

# 查看日志
tail -f user_data/logs/freqtrade.log
```

---

### 方法2：Bot + FreqUI（需要Web界面）

```bash
# 第1步：启动Bot
./start_bot_only.sh

# 第2步：单独启动FreqUI（新终端）
cd /home/dministrator/Newproject/frequi
npm run dev
```

然后浏览器打开显示的URL（通常是 http://127.0.0.1:3000 或其他端口）

---

## 🧪 场景2：回测

### 使用动态币对回测（推荐）

```bash
source .venv/bin/activate

freqtrade backtesting \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231
```

### 使用指定币对回测

```bash
freqtrade backtesting \
    --config user_data/config-backtest-nfx7-top20.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231
```

---

## 🔍 场景3：测试配置

### 测试币对列表生成

```bash
source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

freqtrade test-pairlist \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --quote USDT
```

### 验证配置文件

```bash
source .venv/bin/activate

freqtrade show-config \
    --config user_data/config-custom.json \
    --config user_data/config-private.json
```

---

## 📁 配置文件说明

### ✅ 实盘/回测使用这些文件：

```
实盘：
  --config user_data/config-custom.json        # 主配置
  --config user_data/config-private.json       # 密钥

回测：
  --config user_data/config-custom.json        # 使用动态币对
  或
  --config user_data/config-backtest-*.json   # 使用固定币对
```

### 🔧 配置模块（自动加载）：

通过 `config-custom.json` 的 `add_config_files` 自动加载：

```json
"add_config_files": [
  "../configs/trading_mode-futures.json",           // 期货模式
  "../configs/pairlist-volume-binance-usdt.json",   // 动态币对 ⭐
  "../configs/blacklist-binance.json"                // 黑名单
]
```

---

## ⚙️ 关键配置参数

| 参数 | 当前值 | 说明 |
|------|--------|------|
| `max_open_trades` | 12 | 最大同时持仓（9多+3空）|
| `stake_amount` | unlimited | 仓位大小（无限制=平均分配）|
| `futures_mode_leverage` | 14x | 杠杆倍数 |
| `trading_mode` | futures | 交易模式（期货）|
| `margin_mode` | isolated | 逐仓模式 |
| **动态币对数量** | ~73个 | 自动筛选 |
| **更新频率** | 30分钟 | 自动刷新 |

---

## 📊 符合原作者推荐标准

| 项目 | 原作者推荐 | 当前配置 | 状态 |
|------|-----------|---------|------|
| 币对数量 | 40-80 | ~73 | ✅ |
| 开仓位数 | 6-12 | 12 | ✅ |
| 选择方式 | 动态交易量 | VolumePairList | ✅ |
| 时间周期 | 5m | 5m | ✅ |
| 过滤器 | 多层 | 7层 | ✅ |

---

## 🛑 停止服务

```bash
# 停止Bot
pkill -f "freqtrade trade"

# 停止FreqUI
pkill -f "vite"

# 查看运行状态
ps aux | grep -E "freqtrade|vite" | grep -v grep
```

---

## 📚 详细文档

- **配置详细说明：** [CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md)
- **原项目文档：** https://iterativv.github.io/NostalgiaForInfinity/
- **Freqtrade文档：** https://www.freqtrade.io

---

## 🆘 快速故障排查

### Bot无法启动？
```bash
# 查看日志
tail -50 user_data/logs/freqtrade.log

# 检查配置
freqtrade show-config --config user_data/config-custom.json
```

### FreqUI端口冲突？
```bash
# 清理所有vite进程
pkill -9 -f vite

# 手动启动并查看实际端口
cd /home/dministrator/Newproject/frequi
npm run dev
```

### API无响应？
```bash
# 检查Bot是否运行
ps aux | grep "freqtrade trade"

# 测试API
curl http://127.0.0.1:8082/api/v1/ping
```

---

**最后更新：** 2025-11-06
