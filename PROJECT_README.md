# Freqtrade 项目部署文档

> 这是一个基于 [Freqtrade](https://www.freqtrade.io) 的加密货币交易Bot实例，使用 NostalgiaForInfinityX7 策略进行实盘交易。

---

## 📖 文档导航

| 文档 | 说明 | 适用人群 |
|------|------|---------|
| **[QUICK_START.md](./QUICK_START.md)** | 🚀 快速启动指南 | **所有用户（必读）** |
| [CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md) | 配置文件详解 | 需要修改配置的用户 |
| [BACKTEST_GUIDE.md](./BACKTEST_GUIDE.md) | 回测指南 | 策略优化用户 |
| [CLAUDE.md](./CLAUDE.md) | 开发者指南 | 开发人员 |
| [README.md](./README.md) | 官方Freqtrade文档 | 了解Freqtrade |

---

## ⚡ 快速开始

### 第一次使用？

```bash
# 1. 一键启动Bot + Web UI（推荐）
./ft start --bot --ui -d

# 2. 查看服务状态
./ft status

# 3. 浏览器访问 Web UI
# http://127.0.0.1:3000
# 登录信息：
#   - API地址: http://127.0.0.1:8082
#   - 用户名: freqtrade_user
#   - 密码: freqtrade_pass123
```

**完整指南**: 请阅读 **[QUICK_START.md](./QUICK_START.md)** 📚

---

## 🏗️ 项目架构

### 启动脚本系统

本项目提供了两套启动方式：

#### ⭐ 推荐：模块化脚本系统

```
ft (主控脚本)
├── scripts/start-bot.sh      # Bot启动脚本
├── scripts/start-ui.sh        # UI启动脚本
├── scripts/stop.sh            # 停止脚本
├── scripts/status.sh          # 状态查看脚本
└── lib/common.sh              # 共享函数库
```

**特点**：
- ✅ 模块化设计，职责清晰
- ✅ 优雅的进程管理（避免数据损坏）
- ✅ 精确的端口管理（不误杀其他进程）
- ✅ 实时健康检查
- ✅ 灵活组合（可独立控制每个服务）

**使用方法**：
```bash
./ft start --bot --ui -d    # 启动
./ft status                 # 查看状态
./ft stop --all             # 停止
./ft help                   # 查看帮助
```

#### 兼容：传统一键脚本

```
start_all.sh          # 一键启动Bot和UI
start_bot_only.sh     # 只启动Bot
```

**特点**：
- ✅ 简单直接
- ✅ 一键操作
- ⚠️ 配置固定
- ⚠️ 无法灵活控制单个服务

---

## ⚙️ 配置文件结构

```
user_data/
├── config-custom.json          # 主配置文件（实盘）
├── config-private.json         # 私钥配置（不提交到Git）
├── config-backtest-*.json      # 回测配置文件
└── strategies/
    └── NostalgiaForInfinityX7.py  # 当前使用的策略

configs/                        # 配置模块（自动加载）
├── trading_mode-futures.json  # 期货模式
├── pairlist-volume-binance-usdt.json  # 动态币对筛选
└── blacklist-binance.json     # 黑名单
```

### 当前配置亮点

| 配置项 | 值 | 说明 |
|--------|----|----|
| **交易模式** | 期货 (14倍杠杆) | 使用逐仓模式 |
| **策略** | NostalgiaForInfinityX7 | 经过市场验证的策略 |
| **币对数量** | ~73个 | 动态筛选，每30分钟更新 |
| **最大持仓** | 12个 | 9个多单 + 3个空单 |
| **时间周期** | 5分钟 | 适合短线交易 |

---

## 🔧 常用命令速查

### 启动/停止服务

```bash
# === 使用 ft 脚本（推荐） ===
./ft start --bot --ui -d     # 启动Bot和UI（后台）
./ft start --bot -d          # 只启动Bot
./ft start --ui              # 只启动UI
./ft stop --all              # 停止所有
./ft stop --bot              # 只停止Bot
./ft status                  # 查看状态

# === 使用传统脚本 ===
./start_all.sh               # 一键启动
./start_bot_only.sh          # 只启动Bot
pkill -f "freqtrade trade"   # 手动停止Bot
```

### 查看状态

```bash
# 查看服务运行状态
./ft status

# 查看Bot日志
tail -f user_data/logs/freqtrade.log

# 查看当前交易状态（API）
curl http://127.0.0.1:8082/api/v1/status | python3 -m json.tool

# 查看当前币对列表
curl http://127.0.0.1:8082/api/v1/whitelist | python3 -m json.tool
```

### 回测和优化

```bash
# 激活虚拟环境
source .venv/bin/activate

# 回测（使用动态币对）
freqtrade backtesting \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231

# 测试币对列表生成
freqtrade test-pairlist \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --quote USDT
```

---

## 🔍 两套启动方式对比

| 特性 | `./ft` 脚本系统 | 传统脚本 |
|------|----------------|---------|
| **灵活性** | ⭐⭐⭐⭐⭐ 可独立控制每个服务 | ⭐⭐ 只能全部启动 |
| **健壮性** | ⭐⭐⭐⭐⭐ 优雅停止+健康检查 | ⭐⭐⭐ 暴力kill |
| **配置** | ⭐⭐⭐⭐⭐ 命令行参数 | ⭐⭐ 硬编码在脚本中 |
| **端口管理** | ⭐⭐⭐⭐⭐ 精确识别 | ⭐⭐⭐ 扫描多个端口 |
| **错误处理** | ⭐⭐⭐⭐⭐ 完善的检查 | ⭐⭐⭐ 基础检查 |
| **学习曲线** | 中等 | 低 |
| **推荐场景** | 生产环境、日常使用 | 快速测试 |

**建议**:
- 🌟 **日常使用推荐 `./ft` 系统**（更稳健、更灵活）
- 📦 快速测试可用 `./start_all.sh`（更快上手）

---

## 📊 系统监控

### 查看实时性能

```bash
# CPU和内存使用
top -p $(pgrep -f "freqtrade trade")

# 查看最近的交易
curl http://127.0.0.1:8082/api/v1/trades | python3 -m json.tool

# 查看账户余额
curl http://127.0.0.1:8082/api/v1/balance | python3 -m json.tool
```

### 日志分析

```bash
# 实时查看日志
tail -f user_data/logs/freqtrade.log

# 搜索错误信息
grep -i error user_data/logs/freqtrade.log

# 查看最近50行
tail -n 50 user_data/logs/freqtrade.log
```

---

## 🆘 故障排查

### Bot无法启动

```bash
# 1. 查看详细日志
tail -100 user_data/logs/freqtrade.log

# 2. 验证配置文件
freqtrade show-config \
    --config user_data/config-custom.json \
    --config user_data/config-private.json

# 3. 检查虚拟环境
source .venv/bin/activate
which freqtrade

# 4. 检查端口占用
./ft status
lsof -i :8082
```

### UI无法连接Bot

```bash
# 1. 检查Bot是否运行
ps aux | grep "freqtrade trade"

# 2. 测试Bot API
curl http://127.0.0.1:8082/api/v1/ping

# 3. 检查防火墙（如果在远程服务器）
sudo ufw status
```

### 端口冲突

```bash
# 使用 ft 脚本（自动处理端口冲突）
./ft start --bot --ui -d

# 手动清理端口
lsof -ti :8082 | xargs kill -9   # Bot端口
lsof -ti :3000 | xargs kill -9   # UI端口
```

---

## 📚 详细文档

- **[QUICK_START.md](./QUICK_START.md)** - 详细的启动和使用指南
- **[CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md)** - 配置文件详解
- **[BACKTEST_GUIDE.md](./BACKTEST_GUIDE.md)** - 回测和策略优化
- **[官方文档](https://www.freqtrade.io)** - Freqtrade完整文档
- **[策略文档](https://iterativv.github.io/NostalgiaForInfinity/)** - NostalgiaForInfinity策略说明

---

## 🔐 安全提醒

⚠️ **重要**：
- `config-private.json` 包含API密钥，**永远不要提交到Git**
- 建议使用只读API密钥进行监控
- 交易API密钥应限制IP白名单
- 定期更换API密钥
- 启用交易所的双因素认证

---

## 🤝 贡献与支持

本项目基于开源项目 [Freqtrade](https://github.com/freqtrade/freqtrade) 和 [NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity)。

- **Freqtrade Discord**: https://discord.gg/p7nuUNVfP7
- **官方文档**: https://www.freqtrade.io
- **问题反馈**: 请先查看日志和文档

---

**最后更新**: 2025-01-06
**Freqtrade版本**: 2024.12+
**策略**: NostalgiaForInfinityX7
