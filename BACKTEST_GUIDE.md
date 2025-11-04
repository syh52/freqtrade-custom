# Freqtrade 回测使用指南

## 📊 回测配置说明

### 配置文件

已创建专门的回测配置文件，使用静态交易对列表：

```
user_data/
├── config-backtest.json                          # 回测主配置
└── configs/
    └── pairlist-static-backtest.json            # 静态交易对列表
```

### 交易对列表

回测使用 **34个币安USDT永续合约**（从37个中移除了黑名单的2个）：

```
AAVE, ADA, ALGO, APT, ARB, ATOM, AVAX, BCH, BTC, DOGE,
DOT, ETC, ETH, FIL, HBAR, HYPE, IMX, INJ, LDO, LINK,
LTC, MANA, NEAR, OP, SAND, SEI, SOL, SUI, TIA, TRX,
UNI, WLD, XLM, XRP
```

**已移除**（黑名单）：
- BNB/USDT:USDT
- RUNE/USDT:USDT

---

## 🚀 快速回测

### 基础回测命令

```bash
source .venv/bin/activate
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20241102-20251102
```

### 指定时间范围

```bash
# 最近30天
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241003-20251102

# 最近3个月
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20240802-20251102

# 完整一年
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102
```

---

## 📈 高级回测功能

### 1. 详细模式（查看每笔交易）

```bash
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --breakdown day week month
```

### 2. 导出交易记录

```bash
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --export trades

# 导出文件位置：
# user_data/backtest_results/backtest-result-*.json
```

### 3. 启用缓存（加速重复回测）

```bash
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --cache pairs

# 第二次运行会快很多（使用缓存的技术指标）
```

### 4. 多核心并行回测

```bash
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --cache pairs \
  --jobs 4  # 使用4个CPU核心
```

---

## 📊 查看回测结果

### 1. 命令行查看

回测完成后自动显示：
- 总收益率
- 胜率
- 最大回撤
- 夏普比率
- 总交易次数
- 平均持仓时间

### 2. 生成详细报告

```bash
freqtrade backtesting-show \
  --config user_data/config-backtest.json
```

### 3. 生成图表

```bash
freqtrade plot-dataframe \
  --config user_data/config-backtest.json \
  --strategy NostalgiaForInfinityX7 \
  --pairs BTC/USDT:USDT ETH/USDT:USDT \
  --timerange 20241102-20251102

# 图表保存在：user_data/plot/
```

### 4. 生成盈利图

```bash
freqtrade plot-profit \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102

# 图表保存在：user_data/plot/
```

---

## ⚙️ 回测vs实盘配置差异

| 配置项 | 实盘/Dry Run | 回测 |
|-------|-------------|------|
| 配置文件 | `config.json` | `config-backtest.json` |
| 交易对列表 | `VolumePairList` (动态) | `StaticPairList` (静态) |
| 交易对数量 | 动态（约70个） | 固定（34个） |

### 为什么回测要用静态列表？

1. **可重复性**：相同条件下结果一致
2. **性能要求**：动态列表需要实时市场数据
3. **数据完整性**：确保所有交易对都有历史数据

---

## 🎯 关键回测参数

### 在 config-backtest.json 中设置

当前设置：
- **初始资金**: 10,000 USDT
- **最大持仓**: 10个
- **杠杆倍数**: 10x
- **交易模式**: 期货（逐仓）
- **止损**: -99%（策略自定义止损）
- **时间周期**: 5分钟

---

## 📝 使用示例

### 示例1：快速验证策略

```bash
# 回测最近1个月
source .venv/bin/activate
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241002-20251102
```

### 示例2：完整年度回测并导出

```bash
# 回测完整一年，启用缓存，导出结果
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --cache pairs \
  --export trades \
  --breakdown month
```

### 示例3：对比不同时间段

```bash
# Q1 2025
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20250101-20250331

# Q2 2025
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20250401-20250630
```

---

## ⚠️ 注意事项

### 回测局限性

1. **滑点未完全模拟**：实盘会有更多滑点
2. **资金费率**：期货资金费率影响实盘但回测可能不准确
3. **市场冲击**：大单会影响价格，回测不会模拟
4. **延迟**：实盘有网络延迟，回测是瞬时的

### 最佳实践

1. ✅ **多时间段验证**：测试不同市场环境（牛市、熊市、横盘）
2. ✅ **前视偏差检查**：确保策略不使用"未来数据"
3. ✅ **Walk-forward测试**：分段测试策略稳定性
4. ✅ **保守估计**：实盘收益通常低于回测10-30%
5. ✅ **先小资金实盘**：回测好不代表实盘一定好

---

## 🔍 故障排除

### 问题1：内存不足

```bash
# 减少交易对或缩短时间范围
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20250901-20251102  # 只测试2个月
```

### 问题2：回测太慢

```bash
# 启用缓存和多核心
freqtrade backtesting \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102 \
  --cache pairs \
  --jobs 4
```

### 问题3：找不到数据

```bash
# 检查可用数据
freqtrade list-data --config user_data/config-backtest.json

# 下载缺失数据
freqtrade download-data \
  --config user_data/config-backtest.json \
  --timerange 20241102-20251102
```

---

## 📚 更多资源

- **官方文档**: https://www.freqtrade.io/en/stable/backtesting/
- **策略优化**: https://www.freqtrade.io/en/stable/hyperopt/
- **性能分析**: https://www.freqtrade.io/en/stable/plotting/

---

## 🔄 配置文件内容

### user_data/config-backtest.json

```json
{
  "strategy": "NostalgiaForInfinityX7",
  "add_config_files": [
    "configs/pairlist-static-backtest.json",
    "configs/blacklist-binance.json",
    "config-custom.json",
    "config-private.json"
  ]
}
```

### user_data/configs/pairlist-static-backtest.json

包含34个币安USDT永续合约的静态白名单。

---

**版本信息**:
- Freqtrade: 2025.11-dev
- 策略: NostalgiaForInfinityX7 (原始版本)
- 数据时间范围: 2024-11-02 至 2025-11-02
- 文档更新: 2025-11-02
