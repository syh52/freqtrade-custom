# 🚀 Freqtrade 快速启动指南

## 📋 当前配置状态

✅ **动态币对系统已配置**（符合NostalgiaForInfinity原作者推荐）
- 自动筛选 ~73 个优质币对
- 每30分钟自动更新
- 7层过滤器（黑名单+年龄+价格+价差+波动率）

---

## 🎯 场景1：实盘交易

### ⭐ 推荐方式：使用 ft 主控脚本（模块化架构）

**一键启动Bot + Web UI（后台运行）：**
```bash
./ft start --bot --ui -d
```

**查看服务状态：**
```bash
./ft status
```

**停止所有服务：**
```bash
./ft stop --all
```

**更多命令：**
```bash
# 只启动Bot（后台运行）
./ft start --bot -d

# 只启动Web UI
./ft start --ui

# 指定配置文件和策略
./ft start --bot --config user_data/config-custom.json --strategy NostalgiaForInfinityX7 -d

# 停止指定服务
./ft stop --bot      # 只停止Bot
./ft stop --ui       # 只停止UI

# 重启服务
./ft restart --all   # 重启所有服务
./ft restart --bot   # 只重启Bot

# 查看帮助
./ft help
```

**优势：**
- ✅ 模块化设计，职责清晰
- ✅ 优雅停止进程（避免数据损坏）
- ✅ 精确的端口管理（不误杀其他进程）
- ✅ 实时健康检查（API验证）
- ✅ 灵活组合（可独立启动/停止任意服务）

**Web UI 登录信息：**
- API地址: `http://127.0.0.1:8082`
- 用户名: `freqtrade_user`
- 密码: `freqtrade_pass123`

---

### 方法2：传统一键启动脚本（兼容旧版）

```bash
./start_all.sh
```

**特点：**
- ✅ 一键启动Bot和UI
- ✅ 自动打开浏览器
- ⚠️ 使用固定配置（NostalgiaForInfinityX7策略）
- ⚠️ 无法灵活控制单个服务

---

### 方法3：只启动Bot（无Web界面）

```bash
# 使用ft脚本（推荐）
./ft start --bot -d

# 或使用传统脚本
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

### 方法4：分别启动Bot和UI（高级用户）

```bash
# 第1步：启动Bot
./scripts/start-bot.sh -d

# 第2步：启动FreqUI（新终端）
./scripts/start-ui.sh

# 或手动启动FreqUI
cd /home/dministrator/Newproject/frequi
npm run dev
```

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

### 推荐方式：使用 ft 脚本

```bash
# 停止所有服务
./ft stop --all

# 停止指定服务
./ft stop --bot      # 只停止Bot
./ft stop --ui       # 只停止UI
```

### 传统方式：使用脚本

```bash
# 使用独立脚本
./scripts/start-bot.sh --stop
./scripts/start-ui.sh --stop
```

### 手动方式

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

## 📘 更多文档

- **[PROJECT_README.md](./PROJECT_README.md)** - 项目部署总览和架构说明
- **[CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md)** - 配置文件详解
- **[BACKTEST_GUIDE.md](./BACKTEST_GUIDE.md)** - 回测指南
- **[docs/plans/2025-11-06-script-simplification-design.md](./docs/plans/2025-11-06-script-simplification-design.md)** - 脚本架构设计文档

---

**最后更新：** 2025-01-06
**脚本版本：** ft v2.0（模块化架构）
