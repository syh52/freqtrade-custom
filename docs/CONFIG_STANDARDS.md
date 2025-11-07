# 回测与实盘配置规范

## 核心原则

**🚨 关键规则：回测配置与实盘配置必须完全隔离，永远不要修改实盘配置文件来做回测！**

## 文件结构

```
user_data/
├── config-custom.json              # ❌ 实盘主配置（禁止修改用于回测）
├── config-private.json             # ❌ 实盘API密钥（禁止修改）
├── config-backtest-*.json          # ✅ 回测专用配置（独立文件）
└── configs/
    ├── pairlist-backtest-*.json    # ✅ 回测交易对列表（静态）
    └── pairlist-volume-*.json      # ❌ 实盘动态交易对（不支持回测）
```

## 配置文件命名规范

### 实盘配置（禁止用于回测）
- `config-custom.json` - 实盘主配置
- `config-private.json` - API密钥和敏感信息

### 回测配置（独立管理）
- `config-backtest-<描述>.json` - 通用回测配置
- `config-backtest-realistic.json` - 模拟真实环境
- `config-backtest-<策略名>-<交易对数>pairs.json` - 特定策略回测

**命名建议：**
```
config-backtest-nfx7-55pairs.json       # NostalgiaForInfinityX7策略，55个交易对
config-backtest-realistic-10pos.json    # 真实环境，10个仓位
config-backtest-optimized-custom.json   # 优化参数测试
```

## 配置差异对照

| 配置项 | 实盘 | 回测 | 说明 |
|--------|------|------|------|
| **Pairlist** | VolumePairList（动态） | StaticPairList（静态） | 回测必须用静态列表 |
| **API Keys** | 必需 | 可选 | 回测可用假密钥 |
| **dry_run** | false（真实交易） | true（模拟） | 回测强制dry_run=true |
| **dry_run_wallet** | N/A | 设定初始资金 | 回测起始资金（如10000 USDT） |
| **stoploss_on_exchange** | true（推荐） | false | 回测不支持交易所止损 |
| **Funding fee** | 自动计算 | funding_fee_offset=-8 | 回测需手动配置资金费率 |

## 回测配置模板

### 最小化配置（推荐）

```json
{
  "strategy": "NostalgiaForInfinityX7",
  "add_config_files": [
    "configs/pairlist-backtest-55pairs.json",
    "../configs/blacklist-binance.json",
    "config-custom.json",          // 继承实盘基础配置
    "config-private.json"
  ],
  "max_open_trades": 10,             // 覆盖实盘设置
  "dry_run": true,                   // 强制模拟模式
  "nfi_parameters": {
    "futures_max_open_trades_long": 9,
    "futures_max_open_trades_short": 1
  }
}
```

**优点：** 只覆盖需要测试的参数，其他继承实盘配置，保持一致性。

### 完整独立配置

```json
{
  "strategy": "NostalgiaForInfinityX7",
  "max_open_trades": 10,
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "dry_run": true,
  "dry_run_wallet": 10000,
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      // ... 其他交易对
    ]
  },
  "pairlists": [
    { "method": "StaticPairList" }
  ],
  "order_types": {
    "stoploss_on_exchange": false    // 回测不支持
  },
  "NostalgiaForInfinityX7": {
    "leverage_num": 14
  },
  "nfi_parameters": {
    "futures_max_open_trades_long": 9,
    "futures_max_open_trades_short": 1
  },
  "fee": 0.0004,
  "funding_fee_offset": -8
}
```

**优点：** 完全独立，不依赖实盘配置，参数明确清晰。

## 使用指南

### 1. 实盘启动（禁止使用回测配置）

```bash
# ✅ 正确：使用实盘配置
./ft start --bot -d
./scripts/start-bot.sh -d

# ❌ 错误：使用回测配置启动实盘
./ft start --bot --config user_data/config-backtest-*.json  # 危险！
```

### 2. 回测执行（禁止使用实盘配置）

```bash
# ✅ 正确：使用回测专用配置
freqtrade backtesting \
  --config user_data/config-backtest-realistic.json \
  --timerange 20241001-20241231

# ❌ 错误：直接使用实盘配置回测
freqtrade backtesting \
  --config user_data/config-custom.json  # 会失败（动态pairlist）
```

### 3. 测试不同参数

```bash
# 测试10个仓位
freqtrade backtesting --config user_data/config-backtest-10pos.json

# 测试8个仓位
freqtrade backtesting --config user_data/config-backtest-8pos.json

# 测试不同时间段
freqtrade backtesting --config user_data/config-backtest-realistic.json \
  --timerange 20240101-20240630  # 上半年
```

## 快速检查清单

**修改配置前问自己：**
- [ ] 我要修改的是回测配置还是实盘配置？
- [ ] 实盘Bot正在运行吗？（运行中禁止修改实盘配置）
- [ ] 这个参数会影响下次实盘重启吗？
- [ ] 是否应该创建新的回测配置文件？

**回测前检查：**
- [ ] 使用的是 `config-backtest-*.json` 文件？
- [ ] pairlist 是 `StaticPairList`？
- [ ] `dry_run` 设置为 `true`？
- [ ] `stoploss_on_exchange` 设置为 `false`？

## 常见错误

### ❌ 错误1：修改实盘配置用于回测
```bash
# 错误操作
vim user_data/config-custom.json  # 修改max_open_trades
freqtrade backtesting --config user_data/config-custom.json

# 后果：下次重启实盘Bot时，参数变了！
```

### ✅ 正确做法
```bash
# 创建独立回测配置
cp user_data/config-custom.json user_data/config-backtest-test.json
vim user_data/config-backtest-test.json  # 修改参数
freqtrade backtesting --config user_data/config-backtest-test.json
```

### ❌ 错误2：使用动态pairlist回测
```
Pairlist Handlers VolumePairList do not support backtesting.
```

### ✅ 正确做法
回测配置中使用静态交易对列表：
```json
{
  "exchange": {
    "pair_whitelist": ["BTC/USDT:USDT", "ETH/USDT:USDT", ...]
  },
  "pairlists": [
    { "method": "StaticPairList" }
  ]
}
```

## 最佳实践

### 1. 版本控制
```bash
# 回测配置可以提交到Git
git add user_data/config-backtest-*.json

# 实盘配置永远不要提交（已在.gitignore）
# user_data/config-custom.json  ← 本地修改
# user_data/config-private.json ← 包含密钥，禁止提交
```

### 2. 参数测试流程
```
1. 创建回测配置 → 2. 回测验证 → 3. 分析结果 → 4. 决策 → 5. 修改实盘配置 → 6. 重启Bot
                                                        ↑
                                                只有在这一步才修改实盘配置
```

### 3. 配置文档化
在回测配置中添加注释：
```json
{
  "_description": "回测10个仓位（9多1空）在2024年Q4的表现",
  "_created": "2025-11-06",
  "_purpose": "测试减少做空仓位的影响",
  "max_open_trades": 10,
  ...
}
```

## 紧急恢复

如果误修改了实盘配置：

```bash
# 1. 从Git恢复
git checkout user_data/config-custom.json

# 2. 如果没有Git备份，从回测配置重建
cp user_data/config-backtest-realistic.json user_data/config-custom.json
# 然后手动修改：
# - 改回 VolumePairList
# - 设置 dry_run=false
# - 恢复正确的参数
```

## 总结

| 场景 | 使用配置 | 关键特征 |
|------|----------|----------|
| 实盘交易 | `config-custom.json` | VolumePairList, dry_run=false |
| 回测分析 | `config-backtest-*.json` | StaticPairList, dry_run=true |
| 参数测试 | 新建 `config-backtest-test.json` | 独立文件，不影响实盘 |
| 策略开发 | 新建 `config-backtest-<strategy>.json` | 策略专属配置 |

**记住：实盘配置是生产环境，回测配置是测试环境。永远不要混用！**
