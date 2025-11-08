# Freqtrade Entry and Exit Logic Guide

> 完整解析 Freqtrade 入场和出场逻辑，以及 NostalgiaForInfinityX7 策略机制

**文档版本：** v1.0
**策略版本：** NostalgiaForInfinityX7 v17.1.113
**创建时间：** 2025-11-08

---

## 目录

- [一、Freqtrade 框架层面](#一freqtrade-框架层面)
  - [1.1 入场逻辑核心流程](#11-入场逻辑核心流程)
  - [1.2 出场逻辑核心流程](#12-出场逻辑核心流程)
  - [1.3 IStrategy 接口](#13-istrategy-接口)
- [二、NostalgiaForInfinityX7 策略详解](#二nostalgiaforinfinityx7-策略详解)
  - [2.1 策略配置](#21-策略配置)
  - [2.2 入场模式矩阵](#22-入场模式矩阵)
  - [2.3 入场条件详解](#23-入场条件详解)
  - [2.4 出场逻辑详解](#24-出场逻辑详解)
  - [2.5 加仓逻辑](#25-加仓逻辑)
- [三、核心特色机制](#三核心特色机制)
- [四、Tag vs Signal 概念解析](#四tag-vs-signal-概念解析)
  - [4.1 Tag 142 深度分析](#41-tag-142-深度分析)
- [五、关键文件路径参考](#五关键文件路径参考)

---

## 一、Freqtrade 框架层面

### 1.1 入场逻辑核心流程

**主流程链路：**

```
FreqtradeBot.process() [freqtradebot.py:247]
    ↓
FreqtradeBot.enter_positions() [603行]
    ↓ (遍历白名单交易对)
FreqtradeBot.create_trade() [653行]
    ↓
IStrategy.get_entry_signal() [674行]
    ↓
FreqtradeBot.execute_entry() [863行]
    ↓
Exchange.create_order()
```

#### 关键步骤详解

**1. `process()` 方法** (行 247)
- Bot 的主循环入口
- 刷新市场数据
- 调用 `strategy.analyze()` 分析所有交易对
- 处理现有持仓的出场
- 尝试新的入场机会

**2. `enter_positions()` 方法** (行 603-651)
- 遍历白名单中的所有交易对
- 排除已有持仓的交易对
- 检查全局锁定状态（`is_pair_locked()`）
- 为每个交易对调用 `create_trade()`

**3. `create_trade()` 方法** (行 653-711)
- 获取分析后的数据帧（DataFrame）
- 调用策略的 `get_entry_signal()` 获取入场信号
- 检查交易对是否被锁定
- 计算仓位大小（stake_amount）
- 调用 `execute_entry()` 执行入场订单

**4. `execute_entry()` 方法** (行 863-939)
- 确认入场价格和仓位大小
- 调用策略的 `confirm_trade_entry()` 回调（可选确认）
- 向交易所下单
- 创建 `Trade` 对象并保存到数据库

#### 策略层面的信号生成

在 Bot 调用 `strategy.analyze()` 时：

```python
# 1. 计算技术指标
df = strategy.populate_indicators(df, metadata)

# 2. 生成入场信号
df = strategy.populate_entry_trend(df, metadata)
# 此方法会设置 df["enter_long"] 和 df["enter_short"] 列

# 3. 生成出场信号
df = strategy.populate_exit_trend(df, metadata)
# 此方法会设置 df["exit_long"] 和 df["exit_short"] 列
```

---

### 1.2 出场逻辑核心流程

**主流程链路：**

```
FreqtradeBot.process() [freqtradebot.py:247]
    ↓
FreqtradeBot.exit_positions() [287行]
    ↓ (遍历所有持仓)
FreqtradeBot.handle_trade() [1324行]
    ↓
IStrategy.get_exit_signal() [1345行]
    ↓
FreqtradeBot._check_and_execute_exit() [1359行]
    ↓
IStrategy.should_exit() [1365行]
    ↓
FreqtradeBot.execute_trade_exit()
    ↓
Exchange.create_order()
```

#### 出场条件评估（按优先级）

**`should_exit()` 方法综合评估多种出场条件：**

1. **止损检查 (Stoploss)**
   - 调用 `custom_stoploss()` 获取动态止损值
   - 或使用配置中的固定止损值
   - 优先级最高

2. **ROI 检查 (Return on Investment)**
   - 根据持仓时间检查是否达到最小收益率目标
   - 在 `minimal_roi` 配置中定义

3. **出场信号检查**
   - 检查 `exit_long` 或 `exit_short` 列是否为 True
   - 由 `populate_exit_trend()` 生成

4. **自定义出场检查**
   - 调用 `custom_exit()` 方法
   - 策略可以实现复杂的自定义出场逻辑
   - **NostalgiaForInfinityX7 完全依赖此方法**

#### 出场信号检测

```python
# IStrategy.get_exit_signal() 方法
def get_exit_signal(self, pair: str, timeframe: str, dataframe: DataFrame):
    # 检查最新 K 线的 exit_long 或 exit_short 列
    latest_row = dataframe.iloc[-1]

    if latest_row['exit_long'] == 1:
        return True, 'exit_long_signal'
    elif latest_row['exit_short'] == 1:
        return True, 'exit_short_signal'

    return False, None
```

---

### 1.3 IStrategy 接口

**文件位置：** `freqtrade/strategy/interface.py`

#### 必须实现的方法

| 方法 | 行号 | 功能 |
|------|------|------|
| `populate_indicators()` | 228 | 计算技术指标（RSI、EMA、MACD 等） |
| `populate_entry_trend()` | 246 | 生成入场信号（设置 `enter_long`/`enter_short` 列） |
| `populate_exit_trend()` | 265 | 生成出场信号（设置 `exit_long`/`exit_short` 列） |

#### 可选的自定义方法

| 方法 | 行号 | 功能 | 用途 |
|------|------|------|------|
| `custom_exit()` | 589 | 自定义出场逻辑 | 实现复杂的出场策略 |
| `custom_stoploss()` | 441 | 动态止损 | 根据市场情况调整止损 |
| `custom_roi()` | 472 | 自定义 ROI | 动态调整收益率目标 |
| `adjust_trade_position()` | 649 | DCA/加仓逻辑 | 实现分批建仓或加仓 |
| `confirm_trade_entry()` | 353 | 入场前确认 | 最后一刻确认是否入场 |
| `confirm_trade_exit()` | 389 | 出场前确认 | 最后一刻确认是否出场 |

#### 信号检测方法

**`get_entry_signal()` 方法** (行 1346-1400)
- 检查 `enter_long` 和 `enter_short` 列
- 确保没有冲突信号（同时有入场和出场）
- 返回 `SignalDirection` (LONG/SHORT) 和 `enter_tag`

**`get_exit_signal()` 方法** (行 1313-1344)
- 检查 `exit_long` 和 `exit_short` 列
- 返回是否应该出场及出场标签

**`should_exit()` 方法** (行 1411-1513)
- 综合评估所有出场条件
- 返回 `ExitCheckTuple` 列表
- 包含出场类型和原因

---

## 二、NostalgiaForInfinityX7 策略详解

**文件位置：** `user_data/strategies/NostalgiaForInfinityX7.py`

### 2.1 策略配置

```python
# 基本配置
version = "v17.1.113"
timeframe = "5m"                    # 必须使用 5 分钟时间框架
startup_candle_count = 800          # 需要 800 根 K 线预热
stoploss = -0.99                    # 不使用固定止损（由 custom_exit 控制）
can_short = True                    # 支持做空（期货模式）
position_adjustment_enable = True   # 启用加仓功能

# 多时间框架配置
info_timeframes = ["15m", "1h", "4h", "1d"]  # 辅助时间框架
btc_info_timeframes = ["5m", "15m", "1h", "4h", "1d"]  # BTC 分析时间框架

# 期货模式配置
is_futures_mode = False             # 是否启用期货模式
futures_mode_leverage = 14.0        # 杠杆倍数（当前配置为 14x）
```

#### 推荐配置

- **开放交易数：** 6-12 个
- **交易对数量：** 40-80 个（使用成交量配对列表）
- **配对类型：** 使用稳定币对（USDT/USDC）
- **黑名单：** 排除杠杆代币（如 BTCUP、ETHDOWN 等）
- **配对列表：** 使用 VolumePairList（动态成交量排序）

---

### 2.2 入场模式矩阵

#### 做多（Long）入场模式

| 模式 | Tag 范围 | 条件数量 | 特点 | 适用场景 | 代码行号 |
|------|---------|---------|------|---------|---------|
| **Normal** | 1-13 | 13 | 常规多条件过滤 | 正常市场 | 11854-13395 |
| **Pump** | 21-26 | 6 | 识别强势上涨 | 爆拉行情 | 13947-14057 |
| **Quick** | 41-53 | 13 | 快速入场 | 快速机会 | 14059-15379 |
| **Rebuy** | 61-63 | 3 | 回购加仓 | 价格回调 | 15381-15707 |
| **High Profit** | 81-82 | 2 | 高利润潜力 | 高波动币种 | 未详细记录 |
| **Rapid** | 101-110 | 10 | 极速入场 | 短线机会 | 15709-16788 |
| **Grind** | 120 | 1 | 网格加仓 | 震荡行情 | 16790-16815 |
| **Top Coins** | 141-145 | 5 | 顶级币专用 | 主流币（BTC/ETH 等） | 16817-17014 |
| **Scalp** | 161-163 | 3 | 剥头皮 | 超短线 | 16984-17486 |

**总计：** 9 种模式，56 个具体入场条件

#### 做空（Short）入场模式

| 模式 | Tag 范围 | 条件数量 | 特点 | 适用场景 | 代码行号 |
|------|---------|---------|------|---------|---------|
| **Normal** | 501-504 | 4 | 常规做空 | 下跌趋势 | 17723-18415 |
| **Quick** | 541-543 | 3 | 快速做空 | 快速下跌 | 18417-18855 |
| **Scalp** | 661 | 1 | 剥头皮做空 | 超短线做空 | 19157-19219 |

**总计：** 3 种模式，8 个具体入场条件

#### 模式启用控制

每个条件都有对应的开关参数：

```python
# 示例：启用/禁用特定条件
long_entry_signal_params = {
    "long_entry_condition_1": True,
    "long_entry_condition_2": True,
    # ...
    "long_entry_condition_142": True,  # Tag 142
    # ...
}
```

---

### 2.3 入场条件详解

#### 入场条件结构

每个入场条件包含三个部分：

1. **保护条件 (Protections)**
   - 全局保护开关
   - 模式限制（如只允许特定币种）
   - 空 K 线数量限制

2. **多时间框架过滤 (Multi-Timeframe Filters)**
   - 15m、1h、4h、1d 时间框架的 RSI 过滤
   - AROON 指标的趋势强度检测
   - Stochastic RSI 的超买超卖过滤

3. **入场逻辑 (Entry Logic)**
   - 5m 时间框架的具体入场条件
   - 基于技术指标的组合判断

#### 示例：Normal Mode #1 (Tag 1)

**代码位置：** 行 11854-11996

```python
# Condition #1 - Normal mode (Long)
if long_entry_condition_index == 1:
    # ========== 保护条件 ==========
    long_entry_logic.append(df["num_empty_288"] <= allowed_empty_candles_288)
    long_entry_logic.append(df["protections_long_global"] == True)

    # ========== 多时间框架过滤 ==========
    long_entry_logic.append(
        # 5m & 15m & 1h 下跌，但不过度
        ((df["RSI_3"] > 3.0) | (df["RSI_3_15m"] > 3.0) | (df["RSI_3_change_pct_1h"] > -50.0))
        # 5m & 15m 下跌，但 4h 不过高
        & ((df["RSI_3"] > 3.0) | (df["RSI_3_15m"] > 5.0) | (df["RSI_14_4h"] < 60.0))
        # 15m & 1h 下跌，1h 不过低
        & ((df["RSI_3_15m"] > 3.0) | (df["RSI_3_1h"] > 3.0) | (df["AROONU_14_1h"] < 25.0))
        # ... 更多多时间框架条件（约 30+ 个条件组合）
    )

    # ========== 入场逻辑 (5m) ==========
    long_entry_logic.append(
        (df["RSI_14"] < 36.0)                    # RSI 不能太高
        & (df["AROONU_14"] < 25.0)               # 上升趋势不能太强
        & (df["CMF_20"] < -0.0)                  # 资金流出
        & (df["STOCHRSIk_14_14_3_3"] < 20.0)    # 随机 RSI 超卖
        & (df["ROC_9"] < -3.0)                   # 价格变化率为负
        & (df["close"] < df["SMA_16"] * 0.970)   # 价格低于 SMA 的 97%
    )
```

**条件逻辑：**
- 保护条件 + 多时间框架过滤 + 入场逻辑 = **全部使用 AND 逻辑**（必须全部满足）
- 不同条件之间（如 Condition #1 vs Condition #2）= **使用 OR 逻辑**（满足任一即可）

#### 入场信号生成流程

**`populate_entry_trend()` 方法** (行 11797-19408)

```python
def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
    long_entry_conditions = []
    short_entry_conditions = []

    # 1. 初始化列
    df.loc[:, "enter_tag"] = ""
    df.loc[:, "enter_long"] = 0
    df.loc[:, "enter_short"] = 0

    # 2. 检查运行模式和可用槽位
    current_free_slots = self.config["max_open_trades"] - Trade.get_open_trade_count()

    # 3. 遍历所有启用的做多入场信号
    for enabled_long_entry_signal in self.long_entry_signal_params:
        if self.long_entry_signal_params[enabled_long_entry_signal]:
            long_entry_logic = []
            long_entry_condition_index = int(enabled_long_entry_signal.split("_")[-1])

            # 4. 根据条件索引添加具体逻辑
            if long_entry_condition_index == 1:
                # Condition #1 的所有逻辑
                long_entry_logic.append(...)
            elif long_entry_condition_index == 2:
                # Condition #2 的所有逻辑
                long_entry_logic.append(...)
            # ... 更多条件

            # 5. 合并当前条件的所有逻辑（AND）
            if long_entry_logic:
                item_long_entry = reduce(lambda x, y: x & y, long_entry_logic)
                # 记录触发的条件编号
                df.loc[item_long_entry, "enter_tag"] += f"{long_entry_condition_index} "
                long_entry_conditions.append(item_long_entry)

    # 6. 合并所有启用的入场条件（OR）
    if long_entry_conditions:
        df.loc[:, "enter_long"] = reduce(lambda x, y: x | y, long_entry_conditions)

    # 7. 类似处理做空信号
    # ... (short_entry_conditions)

    return df
```

**关键特点：**
- 每个条件都有唯一的索引号（enter_tag）
- 多个条件可以同时启用（通过参数控制）
- 同一根 K 线可能同时满足多个条件（enter_tag 会包含所有条件编号）
- 条件之间是 OR 关系（满足任一即可入场）

---

### 2.4 出场逻辑详解

#### `populate_exit_trend()` 方法

**代码位置：** 行 11767-11771

```python
def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
    df.loc[:, "exit_long"] = 0   # 不使用基于指标的出场信号
    df.loc[:, "exit_short"] = 0
    return df
```

**重要说明：** NostalgiaForInfinityX7 策略**完全依赖 `custom_exit()` 方法**，不使用传统的 `exit_long`/`exit_short` 信号。

#### `custom_exit()` 方法

**代码位置：** 行 1700-2399

**出场流程：**

```python
def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                current_rate: float, current_profit: float, **kwargs) -> Optional[str]:

    # 1. 获取最新的 K 线数据
    df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    last_candle = df.iloc[-1]
    previous_candles = df.iloc[-2:-7]

    # 2. 解析入场标签（确定使用的入场模式）
    enter_tags = trade.enter_tag.split() if trade.enter_tag else []

    # 3. 计算当前盈亏
    filled_entries = trade.select_filled_orders(trade.entry_side)
    filled_exits = trade.select_filled_orders(trade.exit_side)
    profit_stake, profit_ratio, profit_current_stake_ratio, profit_init_ratio = \
        self.calc_total_profit(trade, filled_entries, filled_exits, current_rate)

    # 4. 根据入场模式调用对应的出场函数
    # ========== 做多出场 ==========
    if trade.is_short == False:
        if any(c in self.long_normal_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_normal(
                pair, current_rate, profit_init_ratio, max_profit,
                max_loss, last_candle, previous_candles, trade, current_time
            )
        elif any(c in self.long_pump_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_pump(...)
        elif any(c in self.long_quick_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_quick(...)
        elif any(c in self.long_rebuy_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_rebuy(...)
        elif any(c in self.long_rapid_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_rapid(...)
        elif any(c in self.long_grind_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_grind(...)
        elif any(c in self.long_top_coins_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_top_coins(...)
        elif any(c in self.long_scalp_mode_tags for c in enter_tags):
            sell, signal_name = self.long_exit_scalp(...)

    # ========== 做空出场 ==========
    else:
        if any(c in self.short_normal_mode_tags for c in enter_tags):
            sell, signal_name = self.short_exit_normal(...)
        elif any(c in self.short_quick_mode_tags for c in enter_tags):
            sell, signal_name = self.short_exit_quick(...)
        elif any(c in self.short_scalp_mode_tags for c in enter_tags):
            sell, signal_name = self.short_exit_scalp(...)

    # 5. 返回出场信号
    if sell and signal_name:
        return f"{signal_name} ({enter_tag})"

    return None
```

#### 出场函数结构

**以 `long_exit_normal()` 为例** (行 19447-19488)

```python
def long_exit_normal(self, pair, current_rate, profit_init_ratio,
                     max_profit, max_loss, last_candle, previous_candles,
                     trade, current_time):
    sell = False
    signal_name = None

    # 仅在盈利时检查某些出场信号
    if profit_init_ratio > 0.0:
        # 1. 原始出场信号 (Original exit signals)
        sell, signal_name = self.long_exit_signals(
            self.long_normal_mode_name, profit_init_ratio, max_profit, max_loss,
            last_candle, previous_candles, trade, current_time, True
        )

        # 2. 主要出场信号 (Main exit signals)
        if not sell:
            sell, signal_name = self.long_exit_main(
                self.long_normal_mode_name, profit_init_ratio, max_profit, max_loss,
                last_candle, previous_candles, trade, current_time, True
            )

        # 3. Williams R 出场信号
        if not sell:
            sell, signal_name = self.long_exit_williams(
                self.long_normal_mode_name, profit_init_ratio, max_profit, max_loss,
                last_candle, previous_candles, trade, current_time, True
            )

        # 4. 其他模式特定的出场检查...

    return sell, signal_name
```

#### 出场信号类型

NostalgiaForInfinityX7 使用多种出场信号（分层检测）：

1. **止损信号 (Stop-loss signals)**
   - 基于亏损幅度
   - 考虑持仓时间
   - 根据入场模式使用不同阈值

2. **盈利目标信号 (Profit signals)**
   - 达到预设盈利率后触发
   - 动态调整盈利目标
   - 考虑最大盈利回撤

3. **技术指标信号 (Technical signals)**
   - RSI 超买（如 RSI > 80）
   - EMA 交叉（死叉）
   - Williams R 超买

4. **趋势反转信号 (Trend reversal signals)**
   - AROON 指标反转
   - CMF（资金流）转负
   - 连续 K 线收盘价下降

5. **时间止损信号 (Time-based signals)**
   - 持仓时间过长且未盈利
   - 避免长期占用资金

#### 出场阈值配置

```python
# 止损阈值（不同模式）
stop_threshold_spot = 0.10              # 现货常规模式 10%
stop_threshold_futures = 0.10           # 合约常规模式 10%
stop_threshold_rapid_spot = 0.20        # 快速模式 20%
stop_threshold_grind_spot = 0.15        # 磨单模式 15%
stop_threshold_scalp_spot = 0.20        # 剥头皮模式 20%
stop_threshold_top_coins_spot = 0.10    # 顶级币模式 10%

# 盈利目标示例
profit_threshold_1 = 0.05               # 5% 盈利
profit_threshold_2 = 0.10               # 10% 盈利
profit_threshold_3 = 0.20               # 20% 盈利
```

---

### 2.5 加仓逻辑

**方法：** `adjust_trade_position()` (行 2401-2686)

#### 支持的加仓模式

**1. Rebuy Mode（回购模式）**

- **Tag 范围：** 61-63
- **触发条件：** 价格相对初始入场价下跌一定幅度
- **加仓次数：** 最多 2 次（总共 3 次入场）
- **加仓金额：** 通常与初始仓位相同

**逻辑示例：**
```python
# 第一次加仓（Tag 62）
if (current_rate < trade.open_rate * 0.98) and (len(filled_entries) == 1):
    return stake_amount  # 在价格下跌 2% 时加仓

# 第二次加仓（Tag 63）
if (current_rate < trade.open_rate * 0.96) and (len(filled_entries) == 2):
    return stake_amount  # 在价格下跌 4% 时再次加仓
```

**2. Grind Mode（磨单模式 / 网格模式）**

- **Tag：** 120
- **触发条件：** 价格持续下跌，多次小幅加仓
- **加仓次数：** 可配置，通常 5-10 次
- **加仓金额：** 每次加仓金额递增

**支持的版本：**
- **Grind V2** (行 37307)
- **Grind V3** (行 39717)
- **Grind Original** (行 41045)

**Grind Mode 特点：**
```python
# 多次小额加仓
max_grind_entries = 10  # 最多 10 次加仓

# 动态计算加仓金额
for grind_entry in range(1, max_grind_entries + 1):
    # 每次加仓的价格阈值
    if current_rate < (last_entry_rate * (1 - grind_derisk * grind_entry)):
        # 计算加仓金额（递增）
        stake_amount = initial_stake * (1 + 0.1 * grind_entry)
        return stake_amount
```

**3. 加仓逻辑流程**

```python
def adjust_trade_position(self, trade: Trade, current_time: datetime,
                          current_rate: float, current_profit: float,
                          min_stake: Optional[float], max_stake: float,
                          current_entry_rate: float, current_exit_rate: float,
                          current_entry_profit: float, current_exit_profit: float,
                          **kwargs) -> Optional[float]:

    # 1. 检查是否启用加仓
    if not self.position_adjustment_enable:
        return None

    # 2. 解析入场标签
    enter_tags = trade.enter_tag.split() if trade.enter_tag else []

    # 3. 获取已填充的入场订单
    filled_entries = trade.select_filled_orders(trade.entry_side)

    # 4. 根据入场模式决定加仓策略
    if any(c in self.long_rebuy_mode_tags for c in enter_tags):
        # Rebuy 模式加仓逻辑
        if len(filled_entries) < 3:  # 最多 3 次入场
            # 检查价格下跌幅度
            if current_rate < trade.open_rate * (1 - self.rebuy_threshold):
                return self.calculate_rebuy_stake(...)

    elif any(c in self.long_grind_mode_tags for c in enter_tags):
        # Grind 模式加仓逻辑
        return self.grind_adjust_trade_position(...)

    return None
```

#### 加仓保护机制

```python
# 最大加仓次数限制
max_entries = 10

# 最大仓位限制
max_total_stake = self.wallets.get_total_stake_amount() * 0.5  # 不超过总资金的 50%

# 加仓间隔时间
min_time_between_entries = timedelta(minutes=5)

# 价格变化阈值
min_price_change_for_entry = 0.02  # 至少下跌 2%
```

---

## 三、核心特色机制

### 3.1 多时间框架分析

策略使用 **5 个时间框架** 进行综合分析：

```python
timeframe = "5m"  # 主时间框架（用于入场和出场判断）

# 辅助时间框架（用于过滤信号）
info_timeframes = ["15m", "1h", "4h", "1d"]

# BTC 分析时间框架（用于市场整体趋势判断）
btc_info_timeframes = ["5m", "15m", "1h", "4h", "1d"]
```

**优势：**
- ✅ 过滤掉短期噪音，提高信号质量
- ✅ 识别更大周期的趋势，避免逆势交易
- ✅ 避免在长期下跌趋势中做多
- ✅ 结合 BTC 走势判断整体市场状态

**示例：多时间框架 RSI 过滤**
```python
# 5m & 15m & 1h 都不能过度下跌
((df["RSI_3"] > 3.0) | (df["RSI_3_15m"] > 3.0) | (df["RSI_3_1h"] > 10.0))
# 15m & 4h 不能同时高位
& ((df["RSI_3_15m"] > 5.0) | (df["RSI_14_4h"] < 70.0))
```

---

### 3.2 动态模式切换

策略根据**币种特征**和**市场条件**动态选择入场模式：

```python
# 1. Grind 模式仅适用于特定币种列表
grind_mode_coins = ["BTC", "ETH", "BNB", "SOL", "XRP"]
is_pair_long_grind_mode = metadata["pair"].split("/")[0] in self.grind_mode_coins

# 2. Top Coins 模式仅适用于顶级币种
top_coins_mode_coins = ["BTC", "ETH", "BNB", "SOL"]
is_pair_long_top_coins_mode = metadata["pair"].split("/")[0] in self.top_coins_mode_coins

# 3. 根据市场波动性选择模式
if market_volatility > high_threshold:
    # 使用 Scalp 或 Rapid 模式
    pass
elif market_volatility < low_threshold:
    # 使用 Grind 模式
    pass
```

**模式选择逻辑：**
- **Normal Mode：** 通用模式，适用于所有币种
- **Top Coins Mode：** 仅限 BTC、ETH 等主流币，条件更宽松
- **Grind Mode：** 仅限稳定币种，使用网格加仓
- **Scalp/Rapid Mode：** 高波动币种，快速进出

---

### 3.3 保护机制

#### 1. 全局保护开关

```python
df["protections_long_global"] = True  # 允许做多
df["protections_short_global"] = True  # 允许做空
```

**用途：**
- 在极端市场条件下（如闪崩、极端上涨）暂停入场
- 可手动或通过外部信号控制

#### 2. 空 K 线保护

```python
# 计算过去 288 根 K 线中的空 K 线数量（24 小时 * 12 个 5 分钟）
df["num_empty"] = df["volume"].rolling(window=288).apply(
    lambda x: (x == 0).sum()
)

# 限制
allowed_empty_candles_288 = 20  # 最多允许 20 根空 K 线

# 在入场条件中使用
df["num_empty_288"] <= allowed_empty_candles_288
```

**用途：**
- 避免在交易量过低、流动性差的币对上交易
- 防止滑点过大或无法成交

#### 3. 交易对锁定机制

```python
# 框架自动锁定交易对
if trade_loss > max_acceptable_loss:
    self.lock_pair(pair, until=current_time + timedelta(hours=24))
```

**锁定场景：**
- 交易亏损超过阈值
- 连续止损
- 检测到异常价格波动

**效果：**
- 在锁定期间不会在该交易对上开新仓
- 避免在问题币对上重复亏损

---

### 3.4 分层止损策略

策略使用**基于模式的动态止损**，而非固定止损：

```python
# 不同模式的止损阈值
stop_threshold_spot = 0.10              # 现货常规模式：-10%
stop_threshold_futures = 0.10           # 合约常规模式：-10%
stop_threshold_pump_spot = 0.10         # 泵模式：-10%
stop_threshold_quick_spot = 0.10        # 快速模式：-10%
stop_threshold_rebuy_spot = 0.15        # 回购模式：-15%（允许更大回撤）
stop_threshold_rapid_spot = 0.20        # 快速模式：-20%
stop_threshold_grind_spot = 0.15        # 磨单模式：-15%
stop_threshold_scalp_spot = 0.20        # 剥头皮：-20%
stop_threshold_top_coins_spot = 0.10    # 顶级币：-10%
```

**止损在 `custom_exit()` 中动态计算，考虑：**
1. **当前亏损幅度**
2. **持仓时间**（持仓时间越长，容忍度越低）
3. **入场模式**（不同模式有不同容忍度）
4. **市场波动性**（高波动允许更大回撤）
5. **最大盈利回撤**（曾经盈利过但回撤过多）

**示例：动态止损逻辑**
```python
# 如果曾经盈利 5% 以上，但现在回撤到亏损 2%，触发止损
if max_profit > 0.05 and current_profit < -0.02:
    return "exit_profit_drawdown"

# 如果持仓超过 24 小时且亏损超过 8%，触发止损
if holding_time > timedelta(hours=24) and current_profit < -0.08:
    return "exit_time_stoploss"
```

---

### 3.5 期货模式支持

```python
# 期货模式配置
is_futures_mode = False              # 是否启用期货模式
futures_mode_leverage = 14.0         # 杠杆倍数（当前配置为 14x）

# 仓位限制
futures_max_open_trades_long = 9     # 做多最多 9 个仓位
futures_max_open_trades_short = 3    # 做空最多 3 个仓位

# 保证金模式
futures_margin_mode = "isolated"     # 逐仓模式
```

**期货特定逻辑：**

1. **杠杆管理**
   ```python
   # 根据币种调整杠杆
   if pair in high_volatility_pairs:
       leverage = 10.0  # 高波动币种降低杠杆
   else:
       leverage = 14.0  # 常规杠杆
   ```

2. **做空策略**
   - 支持 3 种做空模式（Normal, Quick, Scalp）
   - 做空条件通常比做多更严格
   - 做空仓位数量限制更少

3. **风险管理**
   ```python
   # 期货模式下更严格的止损
   if is_futures_mode:
       stop_threshold = stop_threshold * 0.8  # 降低 20%
   ```

---

## 四、Tag vs Signal 概念解析

### 信号（Signal）和标签（Tag）的区别

这是理解 Freqtrade 策略的关键概念：

| 概念 | 定义 | 数据类型 | 存储位置 | 作用 |
|------|------|---------|---------|------|
| **Signal（信号）** | 表示"应该入场"或"应该出场" | Boolean (True/False 或 1/0) | DataFrame 的 `enter_long`/`enter_short`/`exit_long`/`exit_short` 列 | Bot 根据此决定是否执行交易 |
| **Tag（标签）** | 记录"哪个条件触发了信号" | String (如 "1", "142", "1 42 53") | DataFrame 的 `enter_tag` 列，Trade 对象的 `enter_tag` 属性 | 帮助出场逻辑选择对应的出场策略 |

### 工作流程示例

假设我们分析 BTC/USDT：

```
1. 策略执行 populate_entry_trend()
   ↓
2. 检查 Condition #1（Normal Mode）
   ✅ 所有条件满足
   → df.loc[满足行, "enter_long"] = 1
   → df.loc[满足行, "enter_tag"] = "1"
   ↓
3. 检查 Condition #142（Top Coins Mode）
   ✅ 所有条件满足（BTC 在顶级币列表中）
   → df.loc[满足行, "enter_long"] = 1（已经是 1 了）
   → df.loc[满足行, "enter_tag"] += "142"  # 现在是 "1 142"
   ↓
4. Bot 检测到 enter_long == 1
   → 决定入场
   → 创建 Trade 对象，保存 enter_tag = "1 142"
   ↓
5. 出场时，custom_exit() 读取 trade.enter_tag = "1 142"
   → 识别到 "1" 属于 long_normal_mode_tags
   → 识别到 "142" 属于 long_top_coins_mode_tags
   → 优先使用 long_exit_normal()（因为 "1" 在前）
```

### 为什么需要 Tag？

**1. 出场策略匹配**
- 不同入场模式需要不同的出场策略
- Tag 告诉出场逻辑应该使用哪种出场函数

**2. 性能追踪**
- 可以统计哪些入场条件表现最好
- 分析不同模式的胜率和盈利率

**3. 调试和优化**
- 快速定位是哪个条件触发了入场
- 针对性地优化特定条件

**4. 多条件同时触发**
- 一根 K 线可能同时满足多个条件
- Tag 记录了所有满足的条件

---

### 4.1 Tag 142 深度分析

#### Tag 142 的定义

**Tag 142** 是 **Top Coins Mode（顶级币种模式）** 的第 2 个入场条件。

**文件位置：** `user_data/strategies/NostalgiaForInfinityX7.py:16852-16895`

**模式分类：**
```python
# Top Coins Mode 包含 5 个条件
long_top_coins_mode_tags = ["141", "142", "143", "144", "145"]
```

#### Tag 142 的完整逻辑

```python
# Condition #142 - Top Coins mode (Long)
if long_entry_condition_index == 142:

    # ========== 1. 保护条件 ==========
    # 必须是顶级币种
    long_entry_logic.append(is_pair_long_top_coins_mode)
    # 空 K 线数量限制
    long_entry_logic.append(df["num_empty_288"] <= allowed_empty_candles_288)
    # 全局保护开关
    long_entry_logic.append(df["protections_long_global"] == True)

    # ========== 2. 多时间框架过滤 ==========
    long_entry_logic.append(
        # 15m & 1h & 4h 下跌，但不过度
        ((df["RSI_3_15m"] > 3.0) | (df["RSI_3_1h"] > 3.0) | (df["RSI_3_4h"] > 15.0))
        # 15m & 1h 下跌，4h 不能太高
        & ((df["RSI_3_15m"] > 3.0) | (df["RSI_3_1h"] > 40.0) | (df["AROONU_14_1h"] < 85.0))
        # 15m & 1h 下跌，4h AROON 不能太高
        & ((df["RSI_3_15m"] > 5.0) | (df["RSI_3_1h"] > 15.0) | (df["AROONU_14_4h"] < 85.0))
        # 15m & 4h 下跌，15m AROON 适中
        & ((df["RSI_3_15m"] > 5.0) | (df["RSI_3_4h"] > 20.0) | (df["AROONU_14_15m"] < 60.0))
        # 15m & 1h 下跌，4h AROON 不能太高
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_1h"] > 10.0) | (df["AROONU_14_4h"] < 85.0))
        # 15m & 1h 下跌，1h Stochastic RSI 不能太高
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_1h"] > 15.0) | (df["STOCHRSIk_14_14_3_3_1h"] < 50.0))
        # 15m & 1h 下跌，15m AROON 适中
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_1h"] > 20.0) | (df["AROONU_14_15m"] < 60.0))
        # 15m & 4h 下跌，15m AROON 不能太高
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_4h"] > 30.0) | (df["AROONU_14_15m"] < 70.0))
        # 15m & 4h 下跌，15m AROON 不能太高
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_4h"] > 20.0) | (df["AROONU_14_15m"] < 70.0))
        # 15m & 4h 下跌，4h AROON 不能太高
        & ((df["RSI_3_15m"] > 10.0) | (df["RSI_3_4h"] > 20.0) | (df["AROONU_14_4h"] < 50.0))
        # 15m & 4h 下跌，15m AROON 不能太高
        & ((df["RSI_3_15m"] > 15.0) | (df["RSI_3_4h"] > 15.0) | (df["AROONU_14_15m"] < 70.0))
        # 1h & 4h 下跌，15m Stochastic RSI 适中
        & ((df["RSI_3_1h"] > 5.0) | (df["RSI_3_4h"] > 25.0) | (df["STOCHRSIk_14_14_3_3_15m"] < 60.0))
        # 1h & 4h 下跌，15m Stochastic RSI 不能太高
        & ((df["RSI_3_1h"] > 25.0) | (df["RSI_3_4h"] > 25.0) | (df["STOCHRSIk_14_14_3_3_15m"] < 70.0))
    )

    # ========== 3. 入场逻辑（5m 时间框架）==========
    long_entry_logic.append(
        (df["RSI_3"] > 5.0)                      # RSI_3 不能太低（避免极端下跌）
        & (df["RSI_4"] < 46.0)                   # RSI_4 不能太高（不追高）
        & (df["RSI_20"] < df["RSI_20"].shift(1)) # RSI_20 正在下降（回调中）
        & (df["close"] < df["SMA_16"] * 0.960)   # 价格低于 16 周期 SMA 的 96%（价格偏离）
    )
```

#### Tag 142 的设计理念

**1. 适用币种**
- **仅限顶级币种**（通过 `is_pair_long_top_coins_mode` 限制）
- 默认列表通常包括：BTC、ETH、BNB、SOL 等
- 这些币种流动性好、波动相对稳定

**2. 入场时机**
- **回调入场策略**：在价格回调时入场
- RSI_3 > 5.0 → 避免极端暴跌（可能是闪崩）
- RSI_4 < 46.0 → 不追高，等待回调
- RSI_20 下降 → 确认正在回调
- 价格低于 SMA_16 的 96% → 价格偏离均线，有回归空间

**3. 多时间框架保护**
- **13 层过滤条件**确保不在极端情况下入场
- 重点关注 15m、1h、4h 时间框架的 RSI 和 AROON
- 使用 OR 逻辑提供容错（至少有一个时间框架满足即可）

**4. 技术指标组合**
- **RSI（相对强弱指数）**：判断超买超卖
- **AROON（阿隆指标）**：判断趋势强度
- **Stochastic RSI（随机 RSI）**：判断动量
- **SMA（简单移动平均线）**：判断价格偏离

#### Tag 142 vs 其他 Top Coins 条件

| Tag | 入场逻辑特点 | 适用场景 |
|-----|-------------|---------|
| 141 | RSI_20 下降 + RSI_3 低 + AROON 低 + 价格低于 SMA | 深度回调 |
| **142** | **RSI_20 下降 + RSI_4 适中 + 价格低于 SMA** | **常规回调（当前条件）** |
| 143 | RSI_3 适中 + Stochastic RSI 低 + EMA 交叉 | EMA 死叉后的反弹 |
| 144 | RSI_20 下降 + RSI_3 低 + AROON 低 + 价格低于 SMA | 强势回调 |
| 145 | RSI_3 低 + Stochastic RSI 低 + EMA 交叉 | 超卖反弹 |

**Tag 142 的独特性：**
- 相比 Tag 141，RSI_3 > 5.0（更保守，避免极端情况）
- 使用 RSI_4 < 46.0 而非 RSI_3（更平滑，减少假信号）
- 不依赖 AROON 或 CMF，专注于 RSI 和 SMA

#### Tag 142 的出场策略

当交易的 `enter_tag` 包含 "142" 时：

```python
# custom_exit() 方法中
if any(c in self.long_top_coins_mode_tags for c in enter_tags):
    sell, signal_name = self.long_exit_top_coins(
        pair, current_rate, profit_init_ratio, max_profit, max_loss,
        last_candle, previous_candles, trade, current_time
    )
```

**`long_exit_top_coins()` 特点：**
- 相比 Normal Mode，允许更大的回撤（因为顶级币种波动性相对小）
- 更倾向于持有，追求更高的盈利率
- 止损阈值：-10%（`stop_threshold_top_coins_spot = 0.10`）

#### 实战示例

**场景：BTC/USDT 在 2024-11-08 14:30**

1. **BTC 在顶级币列表中** ✅
2. **过去 24 小时空 K 线数量 < 20** ✅
3. **全局保护开关开启** ✅
4. **多时间框架检查：**
   - 15m RSI_3 = 12.5 > 3.0 ✅
   - 1h RSI_3 = 25.3 > 3.0 ✅
   - 4h RSI_3 = 45.2 > 15.0 ✅
   - ... (其他 12 个条件也满足) ✅
5. **5m 入场逻辑：**
   - RSI_3 = 8.2 > 5.0 ✅
   - RSI_4 = 38.5 < 46.0 ✅
   - RSI_20 = 42.3，前一根 = 45.1（下降） ✅
   - Close = $35,200，SMA_16 = $36,800，0.96 * $36,800 = $35,328 ✅

**结果：**
- `df.loc[当前行, "enter_long"] = 1`
- `df.loc[当前行, "enter_tag"] = "142"`
- Bot 检测到信号，执行入场

**交易记录：**
```
Pair: BTC/USDT
Enter Rate: $35,200
Enter Tag: 142
Strategy: NostalgiaForInfinityX7
Mode: Top Coins Mode #142
```

#### 如何启用/禁用 Tag 142

在策略文件或配置文件中：

```python
# 启用 Tag 142
long_entry_signal_params = {
    # ... 其他条件
    "long_entry_condition_142": True,  # 启用
    # ... 其他条件
}

# 禁用 Tag 142
long_entry_signal_params = {
    # ... 其他条件
    "long_entry_condition_142": False,  # 禁用
    # ... 其他条件
}
```

#### 性能分析建议

**如何评估 Tag 142 的表现：**

```python
# 使用 Freqtrade 的分析工具
freqtrade backtesting-analysis \
  --analysis-groups enter_tag \
  --enter-reason-list 142

# 查看 Tag 142 的统计数据：
# - 胜率
# - 平均盈利率
# - 平均持仓时间
# - 最大回撤
```

---

## 五、关键文件路径参考

### 框架核心文件

| 组件 | 文件路径 | 关键方法 | 行号 |
|------|---------|---------|------|
| **主 Bot** | `freqtrade/freqtradebot.py` | `process()` | 247 |
|  |  | `enter_positions()` | 603 |
|  |  | `create_trade()` | 653 |
|  |  | `execute_entry()` | 863 |
|  |  | `handle_trade()` | 1324 |
|  |  | `_check_and_execute_exit()` | 1359 |
| **策略接口** | `freqtrade/strategy/interface.py` | `populate_indicators()` | 228 |
|  |  | `populate_entry_trend()` | 246 |
|  |  | `populate_exit_trend()` | 265 |
|  |  | `get_entry_signal()` | 1346 |
|  |  | `get_exit_signal()` | 1313 |
|  |  | `should_exit()` | 1411 |
|  |  | `custom_exit()` | 589 |
|  |  | `custom_stoploss()` | 441 |
|  |  | `adjust_trade_position()` | 649 |
| **交易所** | `freqtrade/exchange/exchange.py` | `create_order()` | - |
| **持久化** | `freqtrade/persistence/models.py` | `Trade` 模型 | - |
| **数据提供者** | `freqtrade/data/dataprovider.py` | `get_analyzed_dataframe()` | - |

### NostalgiaForInfinityX7 策略文件

| 组件 | 文件路径 | 关键方法 | 行号 |
|------|---------|---------|------|
| **策略主文件** | `user_data/strategies/NostalgiaForInfinityX7.py` | 策略配置 | 1-200 |
|  |  | `populate_indicators()` | 201-11765 |
|  |  | `populate_exit_trend()` | 11767-11771 |
|  |  | `populate_entry_trend()` | 11797-19408 |
|  |  | `custom_exit()` | 1700-2399 |
|  |  | `adjust_trade_position()` | 2401-2686 |
| **做多入场** | 同上 | Normal Mode (1-13) | 11854-13395 |
|  |  | Pump Mode (21-26) | 13947-14057 |
|  |  | Quick Mode (41-53) | 14059-15379 |
|  |  | Rebuy Mode (61-63) | 15381-15707 |
|  |  | Rapid Mode (101-110) | 15709-16788 |
|  |  | Grind Mode (120) | 16790-16815 |
|  |  | **Top Coins Mode (141-145)** | **16817-17014** |
|  |  | **- Tag 142** | **16852-16895** |
|  |  | Scalp Mode (161-163) | 16984-17486 |
| **做空入场** | 同上 | Normal Mode (501-504) | 17723-18415 |
|  |  | Quick Mode (541-543) | 18417-18855 |
|  |  | Scalp Mode (661) | 19157-19219 |
| **做多出场** | 同上 | `long_exit_normal()` | 19447-19488 |
|  |  | `long_exit_pump()` | - |
|  |  | `long_exit_quick()` | - |
|  |  | `long_exit_rebuy()` | - |
|  |  | `long_exit_rapid()` | - |
|  |  | `long_exit_grind()` | - |
|  |  | `long_exit_top_coins()` | - |
|  |  | `long_exit_scalp()` | - |
| **做空出场** | 同上 | `short_exit_normal()` | - |
|  |  | `short_exit_quick()` | - |
|  |  | `short_exit_scalp()` | - |
| **Grind 加仓** | 同上 | Grind V2 | 37307 |
|  |  | Grind V3 | 39717 |
|  |  | Grind Original | 41045 |

### 配置文件

| 文件 | 路径 | 用途 |
|------|------|------|
| **主配置** | `user_data/config-custom.json` | 主配置文件，加载其他模块 |
| **私有配置** | `user_data/config-private.json` | API 密钥（不入库） |
| **交易模式** | `configs/trading_mode-futures.json` | 期货交易配置 |
| **配对列表** | `configs/pairlist-volume-binance-usdt.json` | 动态配对列表 |
| **黑名单** | `configs/blacklist-binance.json` | 排除的交易对 |

---

## 附录：快速参考

### 常用命令

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 Bot（使用 ft 工具）
./ft start --bot --ui -d

# 停止服务
./ft stop --all

# 查看状态
./ft status

# 测试配对列表
freqtrade test-pairlist \
  --config user_data/config-custom.json \
  --config user_data/config-private.json

# 回测
freqtrade backtesting \
  --config user_data/config-custom.json \
  --config user_data/config-private.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20240101-20241231

# 分析特定 Tag 的表现
freqtrade backtesting-analysis \
  --analysis-groups enter_tag \
  --enter-reason-list 142
```

### 关键概念速查

| 概念 | 简要说明 |
|------|---------|
| **Signal** | Boolean 值，表示应该入场/出场 |
| **Tag** | String，记录哪个条件触发了信号 |
| **Entry Mode** | 入场模式（Normal, Pump, Quick 等） |
| **Custom Exit** | 自定义出场逻辑，优先级高于基于指标的出场 |
| **Adjust Position** | 加仓逻辑（Rebuy, Grind） |
| **Protection** | 保护机制（全局保护、空 K 线保护、交易对锁定） |
| **Multi-Timeframe** | 多时间框架分析（5m/15m/1h/4h/1d） |
| **Dynamic Stoploss** | 动态止损（基于模式、持仓时间、盈亏） |

### 技术指标速查

| 指标 | 全称 | 用途 |
|------|------|------|
| **RSI** | Relative Strength Index | 判断超买超卖 |
| **AROON** | Aroon Indicator | 判断趋势强度 |
| **CMF** | Chaikin Money Flow | 判断资金流 |
| **Stochastic RSI** | Stochastic RSI | 判断动量 |
| **ROC** | Rate of Change | 判断价格变化速度 |
| **EMA** | Exponential Moving Average | 指数移动平均线 |
| **SMA** | Simple Moving Average | 简单移动平均线 |
| **Williams %R** | Williams %R | 判断超买超卖 |

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2025-11-08 | 初始版本，完整解析入场出场逻辑和 Tag 142 |

---

**文档作者：** Claude Code
**策略作者：** iterativv (NostalgiaForInfinity)
**项目主页：** https://www.freqtrade.io
**策略文档：** https://iterativv.github.io/NostalgiaForInfinity/
