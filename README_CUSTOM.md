# Freqtrade Custom - NostalgiaForInfinity 6x Leverage

这是基于 [Freqtrade](https://github.com/freqtrade/freqtrade) 和 [NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) 策略的定制版本。

## 🎯 项目特点

- ✅ 基于 NostalgiaForInfinity v17.1.51 最新版本
- 🔥 配置为 **6 倍杠杆**期货交易模式
- 🛡️ 添加了**自定义止损保护**机制
- 📊 支持多种交易模式（Normal, Pump, Quick, Rebuy, Grind, TC, Scalp等）
- 🔄 包含原版 10 倍杠杆版本用于对比

## 📦 包含的策略

| 策略名称 | 文件 | 版本 | 杠杆 | 止损 |
|---------|------|------|------|------|
| `NostalgiaForInfinityX7` | NostalgiaForInfinityX7.py | v17.1.41 | 10x | 自定义 |
| `NostalgiaForInfinityX7_6x` | NostalgiaForInfinityX7_latest.py | v17.1.51-6x | 6x | 自定义 |

## 🛡️ 止损策略

根据不同的交易模式，自动应用不同的止损级别：

- **TC Mode (141, 142)**: 3% 止损 - 高风险模式的严格保护
- **Grind Mode (120)**: 10% 止损 - 允许长期持仓
- **Rebuy Mode (61-63)**: 5% 止损 - 加仓模式保护
- **其他模式**: 5% 止损 - 默认平衡保护

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Freqtrade (已包含在项目中)

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/syh52/freqtrade-custom.git
cd freqtrade-custom

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 安装依赖
pip install -e .

# 4. 创建配置文件
freqtrade new-config --config user_data/config.json

# 5. 下载历史数据
freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT --timeframes 5m --days 30
```

### 运行回测

```bash
# 测试 6 倍杠杆版本（推荐）
freqtrade backtesting \
  --strategy NostalgiaForInfinityX7_6x \
  --timeframe 5m \
  --timerange 20241001-20241031

# 测试 10 倍杠杆版本
freqtrade backtesting \
  --strategy NostalgiaForInfinityX7 \
  --timeframe 5m \
  --timerange 20241001-20241031
```

### 启动 Web UI

```bash
# 使用提供的启动脚本
./start_webui.sh

# 或手动启动
freqtrade webserver --config user_data/config.json
```

## 📚 重要文档

- **[CLAUDE.md](CLAUDE.md)** - 项目开发指南和架构说明
- **[MODIFIED_STRATEGY_SUMMARY.md](MODIFIED_STRATEGY_SUMMARY.md)** - 策略修改详细总结
- **[STRATEGY_COMPARISON_GUIDE.md](STRATEGY_COMPARISON_GUIDE.md)** - 策略版本对比指南

## ⚠️ 风险警示

**重要提示：** 这是一个期货交易策略，使用杠杆会放大盈亏。

- ⚡ 6 倍杠杆意味着收益和风险都放大 6 倍
- 📉 爆仓风险：当亏损达到约 16.67% 时可能爆仓
- 🛡️ 自定义止损提供了保护，但仍需谨慎
- 💡 **强烈建议先进行回测和模拟交易**

### 建议的使用流程

1. ✅ 先进行充分的回测（至少 3-6 个月数据）
2. ✅ 使用干运行模式测试至少 1-2 周
3. ✅ 从小额资金开始实盘测试
4. ✅ 密切监控表现并及时调整

## 🔧 配置建议

### 保守配置（新手推荐）

```json
{
  "strategy": "NostalgiaForInfinityX7_6x",
  "max_open_trades": 3,
  "stake_amount": 100,
  "dry_run": true
}
```

### 激进配置（仅限有经验用户）

```json
{
  "strategy": "NostalgiaForInfinityX7_6x",
  "max_open_trades": 12,
  "stake_amount": "unlimited",
  "dry_run": false
}
```

## 🧪 测试工具

项目包含了几个测试脚本：

```bash
# 策略对比测试
./test_strategy_comparison.sh

# 手动仓位测试
./manual_position_test.sh
```

## 📊 与原项目的差异

本项目基于以下两个优秀的开源项目：

- **Freqtrade**: https://github.com/freqtrade/freqtrade
- **NostalgiaForInfinity**: https://github.com/iterativv/NostalgiaForInfinity

主要修改：
1. 将杠杆从 3 倍调整为 6 倍（或 10 倍）
2. 添加了基于交易模式的自定义止损
3. 启用了期货交易模式
4. 添加了策略对比和测试工具

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目遵循 GPL-3.0 许可证（继承自 Freqtrade 和 NostalgiaForInfinity）。

## 🙏 致谢

- [Freqtrade](https://github.com/freqtrade/freqtrade) - 优秀的加密货币交易机器人框架
- [NostalgiaForInfinity](https://github.com/iterativv/NostalgiaForInfinity) - 强大的交易策略
- 所有贡献者和社区成员

## ⚖️ 免责声明

本软件仅供教育和研究目的。不要冒险投入您无法承受损失的资金。使用本软件的风险由您自己承担。作者和所有关联方不对您的交易结果承担任何责任。

在投入真实资金之前，务必：
- 充分理解策略的工作原理
- 进行充分的回测
- 从模拟交易开始
- 了解并接受可能的损失

**加密货币交易存在高风险，可能不适合所有投资者。**

---

**最后更新**: 2025-11-02
**维护者**: [@syh52](https://github.com/syh52)
