# 决策日志系统实现计划

**创建时间**: 2025-11-08
**目标**: 通过运行时Hook记录回测时的决策过程，实现100%准确的决策还原

---

## 🎯 核心目标

在回测时自动记录每笔交易的：
1. **入场时刻的所有技术指标值**
2. **出场时刻的所有技术指标值**
3. **决策元数据**（tag、pair、timestamp等）

在复盘时直接读取这些记录，无需：
- ❌ 手动定义每个Tag的条件逻辑
- ❌ 担心策略代码更新后不同步
- ❌ 猜测当时的技术指标值

---

## 🏗️ 技术方案

### 选择：方式B - Decorator包装（半侵入式）

**核心思路**：
1. 创建策略的子类 `NostalgiaForInfinityX7WithLogging`
2. 使用装饰器包装 `populate_entry_trend()` 和 `custom_exit()`
3. 在策略执行后，记录决策日志到文件
4. 复盘时读取日志文件

**优势**：
- ✅ 不修改原策略代码
- ✅ 代码清晰易懂
- ✅ 调试友好
- ✅ 符合Python最佳实践

---

## 📋 实现步骤

### 第1阶段：极简版（MVP）⭐

**目标**：记录技术指标快照，不分解条件

#### 1.1 创建决策日志记录器
**文件**: `backtest_analyzer/hooks/decision_logger.py`

功能：
- 将决策记录写入JSONL文件
- 支持入场和出场两种类型
- 记录格式：`{timestamp, pair, type, tag, indicators}`

#### 1.2 创建装饰器
**文件**: `backtest_analyzer/hooks/strategy_decorator.py`

功能：
- `@log_entry_decisions`: 包装 `populate_entry_trend()`
- `@log_exit_decisions`: 包装 `custom_exit()`
- 提取所有技术指标并记录

#### 1.3 创建带日志的策略子类
**文件**: `user_data/strategies/NostalgiaForInfinityX7WithLogging.py`

```python
class NostalgiaForInfinityX7WithLogging(NostalgiaForInfinityX7):
    """带决策日志功能的策略"""

    def __init__(self, config):
        super().__init__(config)
        self.logger = DecisionLogger()

    @log_entry_decisions
    def populate_entry_trend(self, dataframe, metadata):
        return super().populate_entry_trend(dataframe, metadata)

    @log_exit_decisions
    def custom_exit(self, pair, trade, current_time, ...):
        return super().custom_exit(pair, trade, current_time, ...)
```

#### 1.4 创建决策回放器
**文件**: `backtest_analyzer/analyzers/decision_replay.py`

功能：
- 从决策日志文件读取记录
- 根据 `pair + timestamp + tag` 匹配交易
- 提供查询接口给UI

#### 1.5 集成到交易复盘页面
**文件**: `backtest_analyzer/app/pages/5_交易复盘.py`

在"决策过程深度还原"部分：
- 尝试加载对应的决策日志
- 如果存在，直接显示真实的指标值
- 如果不存在，显示提示："需要使用 NostalgiaForInfinityX7WithLogging 重新回测"

---

### 第2阶段：增强版（可选）

**目标**：分解条件，记录每个子条件的评估结果

#### 2.1 条件定义元数据
在策略中添加条件定义（可选的注释或配置）：
```python
# 方式1: 结构化注释
"""
@entry_condition tag=142
@layer1: btc_is_bull_4h, btc_is_bull_1d
@layer2: rsi_14_15m < 36, ha_close_15m > ema_12_15m
@layer3: rsi_14 < 30, close < sma_15 * 0.97
"""

# 方式2: 配置文件
# user_data/conditions_definition.yaml
```

#### 2.2 条件分解引擎
解析条件定义，记录每个子条件的True/False

#### 2.3 决策路径追踪
记录 `custom_exit()` 中的执行路径（哪个if分支被触发）

---

## 📁 文件结构

```
freqtrade/
├── backtest_analyzer/
│   ├── hooks/                          # 🆕 Hook模块
│   │   ├── __init__.py
│   │   ├── decision_logger.py         # 决策日志记录器
│   │   └── strategy_decorator.py      # 装饰器
│   │
│   ├── analyzers/
│   │   ├── decision_replay.py         # 🆕 决策回放器
│   │   ├── entry_decision_analyzer.py # 保留，作为无日志时的fallback
│   │   ├── exit_decision_analyzer.py  # 保留，作为无日志时的fallback
│   │   └── parameter_simulator.py     # 保留
│   │
│   └── app/pages/
│       └── 5_交易复盘.py              # 修改，集成决策回放
│
├── user_data/
│   ├── strategies/
│   │   ├── NostalgiaForInfinityX7.py  # 原策略（不修改）
│   │   └── NostalgiaForInfinityX7WithLogging.py  # 🆕 带日志的子类
│   │
│   └── decision_logs/                  # 🆕 决策日志目录
│       └── decisions_20250108_143022.jsonl
│
└── docs/
    └── DECISION_LOGGING_PLAN.md        # 本文件
```

---

## 🚀 使用流程

### 用户视角

#### Step 1: 使用带日志的策略进行回测
```bash
freqtrade backtesting \
  --strategy NostalgiaForInfinityX7WithLogging \
  --config user_data/config-custom.json \
  --timerange 20250101-20250131
```

**输出**：
- `user_data/backtest_results/backtest-result-*.json` (回测结果)
- `user_data/decision_logs/decisions_*.jsonl` (决策日志) 🆕

#### Step 2: 启动分析器
```bash
./start-analyzer.sh
```

#### Step 3: 复盘交易
1. 加载回测结果（自动匹配对应的决策日志）
2. 进入"交易复盘"页面
3. 查看"决策过程深度还原"标签页
4. 看到**真实的技术指标值和决策过程** ✨

---

## 📊 决策日志格式

### JSONL格式（每行一个JSON对象）

```jsonl
{"timestamp": "2025-01-05 10:35:00", "pair": "BTC/USDT:USDT", "type": "entry", "tag": 142, "data": {"indicators": {"rsi_14": 28.5, "rsi_14_15m": 32.1, "rsi_14_1h": 45.2, "ema_12": 44800.3, "sma_15": 45320.5, "close": 44890.2, "volume": 1234.5}, "decision": "enter"}}

{"timestamp": "2025-01-05 14:22:00", "pair": "BTC/USDT:USDT", "type": "exit", "tag": 142, "data": {"indicators": {"rsi_14": 72.3, "close": 45950.8, "current_profit": 0.0235}, "exit_reason": "profit_target", "decision": "exit"}}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string | ISO格式时间戳 |
| `pair` | string | 交易对 |
| `type` | string | "entry" 或 "exit" |
| `tag` | int | 入场/出场Tag |
| `data.indicators` | object | 所有技术指标的值 |
| `data.decision` | string | "enter" 或 "exit" |
| `data.exit_reason` | string | 出场原因（仅exit类型） |

---

## ✅ 验收标准

### 第1阶段完成标准：

- [ ] 能够用 `NostalgiaForInfinityX7WithLogging` 成功运行回测
- [ ] 生成的决策日志文件格式正确
- [ ] 每笔入场交易都有对应的日志记录
- [ ] 每笔出场都有对应的日志记录
- [ ] 复盘页面能正确加载和显示决策日志
- [ ] UI中显示的技术指标值与日志文件一致

### 测试用例：

1. **基础测试**：回测1个月数据，验证日志文件生成
2. **准确性测试**：随机选择5笔交易，手动验证指标值
3. **覆盖率测试**：确认所有164个Tag都能被正确记录
4. **性能测试**：对比有/无日志的回测时间差异（期望<10%）

---

## 🔧 技术细节

### 装饰器实现要点

```python
def log_entry_decisions(func):
    @wraps(func)
    def wrapper(self, dataframe, metadata):
        # 1. 执行原始策略逻辑
        result_df = func(self, dataframe, metadata)

        # 2. 找出所有入场信号行
        entry_rows = result_df[result_df['enter_long'] == 1]

        # 3. 为每行记录日志
        for idx, row in entry_rows.iterrows():
            self.logger.log_entry(
                timestamp=row['date'],
                pair=metadata['pair'],
                tag=row['enter_tag'],
                indicators=row.to_dict()  # 所有列都记录
            )

        return result_df
    return wrapper
```

### 日志文件大小估算

- 每条日志约500-1000字节（包含~50个技术指标）
- 1个月回测，约5000笔交易 × 2（入场+出场）= 10000条记录
- 文件大小：10000 × 1KB = **10MB**（可接受）

---

## 🚨 潜在问题和解决方案

### 问题1: 日志文件与回测结果如何关联？

**方案**：通过时间戳匹配
- 决策日志文件名包含时间戳：`decisions_20250108_143022.jsonl`
- 回测结果文件名也包含时间戳：`backtest-result-2025-01-08_14-30-22.json`
- 在UI中自动匹配同一时间段的文件

### 问题2: 如果用户忘记用带日志的策略怎么办？

**方案**：优雅降级
- 优先尝试加载决策日志
- 如果找不到，回退到原来的手写条件分析器
- UI中显示提示："此回测未启用决策日志，显示的是基于规则的模拟分析"

### 问题3: 策略执行过程中修改了dataframe会影响日志吗？

**方案**：
- 在装饰器中使用 `row.to_dict()` 立即复制数据
- 不依赖后续的dataframe状态

---

## 📅 开发时间估算

| 任务 | 预计时间 |
|------|----------|
| 1.1 创建决策日志记录器 | 30分钟 |
| 1.2 创建装饰器 | 45分钟 |
| 1.3 创建带日志的策略子类 | 15分钟 |
| 1.4 创建决策回放器 | 30分钟 |
| 1.5 集成到UI | 45分钟 |
| 测试和调试 | 60分钟 |
| **总计** | **3-4小时** |

---

## 🎯 下一步行动

1. ✅ 创建本计划文档
2. ⏳ 获得用户确认
3. ⏳ 实施第1阶段（极简版）
4. ⏳ 测试验证
5. ⏳ 根据反馈决定是否实施第2阶段

---

**备注**：本计划采用**增量迭代**的方式，先实现核心价值（指标快照），再逐步增强（条件分解）。
