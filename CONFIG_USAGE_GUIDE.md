# Freqtrade 配置文件使用规范

> 基于 NostalgiaForInfinity 原作者推荐配置整理

## 📁 配置文件结构

```
freqtrade/
├── configs/                          # 通用配置模块（可复用）
│   ├── trading_mode-futures.json    # 期货交易模式配置
│   ├── pairlist-volume-binance-usdt.json  # 动态币对列表（推荐）
│   └── blacklist-binance.json       # 黑名单过滤
│
└── user_data/
    ├── config-custom.json           # ✅ 实盘主配置
    ├── config-private.json          # 🔐 交易所密钥（不提交Git）
    ├── config-backtest.json         # 回测配置
    └── strategies/
        └── NostalgiaForInfinityX7.py  # 交易策略
```

---

## 🎯 使用场景与配置选择

### 1️⃣ **实盘交易（Live Trading）**

#### ✅ 推荐配置组合（符合原作者规范）

```bash
freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7
```

**配置文件说明：**

| 文件 | 作用 | 关键参数 |
|------|------|---------|
| `config-custom.json` | 主配置 | - `add_config_files`: 自动加载模块配置<br>- `max_open_trades`: 12<br>- `futures_mode_leverage`: 14倍<br>- `dry_run`: **false** |
| `config-private.json` | 交易所密钥 | - `exchange.key`<br>- `exchange.secret`<br>- 代理配置 |

**自动加载的模块（通过 `add_config_files`）：**
- ✅ `configs/trading_mode-futures.json` - 期货模式
- ✅ `configs/pairlist-volume-binance-usdt.json` - **动态币对**（73个，每30分钟更新）
- ✅ `configs/blacklist-binance.json` - 黑名单过滤

**符合原作者推荐：**
- ✅ 6-12 个最大持仓（我们设置12个）
- ✅ 40-80 个交易对（我们动态筛选~73个）
- ✅ 动态交易量选择
- ✅ 多层过滤器（黑名单+年龄+价格+价差+波动率）

---

### 2️⃣ **回测（Backtesting）**

#### 方案A：使用动态币对回测（推荐，更真实）

```bash
freqtrade backtesting \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231
```

**优点：**
- 自动使用动态币对列表（和实盘一致）
- 更接近真实交易情况
- 无需手动指定币对

**注意：** 回测时动态币对会基于历史数据生成列表，可能和实盘实时列表略有不同

---

#### 方案B：使用静态币对回测（精确控制）

如果您想精确控制回测的币对，可以临时修改：

```bash
# 1. 创建回测专用配置
cp user_data/config-custom.json user_data/config-backtest-custom.json

# 2. 编辑 config-backtest-custom.json，修改 add_config_files：
#    将 "pairlist-volume-binance-usdt.json"
#    替换为 "pairlist-backtest-top20.json"（已存在）

# 3. 运行回测
freqtrade backtesting \
    --config user_data/config-backtest-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231
```

---

### 3️⃣ **模拟盘测试（Dry Run）**

```bash
# 临时修改 config-custom.json 中的：
# "dry_run": true

freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7
```

或使用命令行覆盖：
```bash
freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --dry-run
```

---

## 🔧 配置模块详解

### `configs/pairlist-volume-binance-usdt.json` 🌟

**动态币对筛选流程（7层过滤）：**

```
交易所所有币对
    ↓
1️⃣ VolumePairList (前100名交易量)
    ↓
2️⃣ FullTradesFilter (满仓时缩减白名单)
    ↓
3️⃣ AgeFilter (≥60天) ← 过滤新币
    ↓
4️⃣ PriceFilter (≥0.3%) ← 过滤低价币
    ↓
5️⃣ SpreadFilter (≤0.5%) ← 过滤流动性差的
    ↓
6️⃣ RangeStabilityFilter (3%-95%波动) ← 过滤极端波动
    ↓
7️⃣ VolumePairList (最终前80名)
    ↓
最终白名单：~73个优质币对
```

**自动更新：** 每30分钟刷新一次

---

### `configs/blacklist-binance.json`

**自动排除以下币种：**
- 🚫 杠杆代币 (BULL, BEAR, UP, DOWN, 1000*)
- 🚫 粉丝代币 (CHZ, PSG, JUV...)
- 🚫 稳定币交叉对 (USDC/USDT)
- 🚫 问题币种 (LUNA, FTT, USTC...)
- 🚫 低流动性币种

---

## ⚙️ 关键参数对照表

### 实盘配置 vs 原作者推荐

| 参数 | 原作者推荐 | 当前配置 | 状态 |
|------|-----------|---------|------|
| **交易对数量** | 40-80 | 动态~73 | ✅ |
| **最大持仓** | 6-12 | 12 (9多+3空) | ✅ |
| **币对选择** | 动态交易量 | VolumePairList | ✅ |
| **更新频率** | 定期更新 | 每30分钟 | ✅ |
| **黑名单** | 必须 | 已配置 | ✅ |
| **年龄过滤** | 推荐≥60天 | 60天 | ✅ |
| **时间周期** | 5m | 5m | ✅ |
| **杠杆** | 自定义 | 14倍 | ⚠️ 根据风险偏好 |

---

## 🚀 快速启动命令

### 实盘交易
```bash
# 方式1：使用启动脚本
./start_all.sh

# 方式2：手动启动
source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7
```

### 回测
```bash
source .venv/bin/activate
freqtrade backtesting \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    --timerange 20240101-20241231
```

### 测试币对列表
```bash
source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
freqtrade test-pairlist \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --quote USDT
```

---

## 📝 配置修改指南

### 如何调整币对数量？

编辑 `configs/pairlist-volume-binance-usdt.json`：

```json
{
  "pairlists": [
    {
      "method": "VolumePairList",
      "number_assets": 100,  // ← 修改这里（初始筛选数量）
      ...
    },
    ...
    {
      "method": "VolumePairList",
      "number_assets": 80,   // ← 修改这里（最终数量）
      ...
    }
  ]
}
```

### 如何添加/删除黑名单币种？

编辑 `configs/blacklist-binance.json`：

```json
{
  "exchange": {
    "pair_blacklist": [
      "(BNB)/.*",           // ← 添加新的正则表达式
      "YOUR_COIN/USDT:USDT" // ← 或精确币对名称
    ]
  }
}
```

### 如何切换到现货交易？

1. 修改 `configs/trading_mode-futures.json` 为 `trading_mode-spot.json`
2. 或在 `config-custom.json` 中直接设置：
   ```json
   {
     "trading_mode": "spot",
     "margin_mode": null
   }
   ```

---

## ⚠️ 重要注意事项

### 🔴 实盘前必查

1. ✅ 确认 `dry_run: false`
2. ✅ 确认交易所API密钥正确
3. ✅ 确认有足够的可用余额
4. ✅ 测试币对列表生成正常：`freqtrade test-pairlist ...`
5. ✅ 确认策略参数正确

### 🔐 安全建议

- ⚠️ **永远不要** 提交 `config-private.json` 到Git
- ⚠️ 建议添加到 `.gitignore`
- ⚠️ API密钥只赋予必要权限（交易权限，不要提现权限）

### 📊 监控建议

```bash
# 查看实时日志
tail -f user_data/logs/freqtrade.log

# 查看当前交易
curl http://127.0.0.1:8082/api/v1/status | python3 -m json.tool

# 查看币对白名单
curl http://127.0.0.1:8082/api/v1/whitelist | python3 -m json.tool
```

---

## 📚 参考资料

- **NostalgiaForInfinity原项目：** https://github.com/iterativv/NostalgiaForInfinity
- **原作者文档：** https://iterativv.github.io/NostalgiaForInfinity/
- **Freqtrade官方文档：** https://www.freqtrade.io

---

## 🆘 常见问题

### Q: 回测和实盘币对不一致？
**A:** 正常现象。动态币对列表基于实时/历史交易量，会随市场变化。

### Q: 如何固定币对列表？
**A:** 创建静态币对配置文件，参考 `configs/pairlist-backtest-top20.json`

### Q: 杠杆倍数如何修改？
**A:** 在 `config-custom.json` 中修改 `futures_mode_leverage`

### Q: 黑名单不生效？
**A:** 检查 `add_config_files` 是否正确引用 `blacklist-binance.json`

---

**最后更新：** 2025-11-06
**配置版本：** NostalgiaForInfinityX7 + 动态币对系统
