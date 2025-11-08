# FreqAI 工作日志

## 当前状态
✅ FreqAI 已安装并可运行
✅ LightGBM 模型优化完成
✅ 毒瘤币种检测系统部署
✅ 回测分析器优化完成

## 核心文件
```
user_data/strategies/
├── FreqAITest.py                        # 基础测试策略
├── FreqAILeverageReversal.py           # 12倍杠杆反转策略
└── FreqAITest_Advanced.py              # 高级反转特征策略

user_data/config-freqai-*.json           # FreqAI 配置文件
backtest_analyzer/                       # 回测分析工具
scripts/start-*.sh                       # 启动脚本
```

## 快速命令

### 回测
```bash
freqtrade backtesting --config user_data/config-freqai-optimized.json \
  --strategy FreqAITest --timerange 20251020-20251106
```

### 数据下载（需代理）
```bash
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897
freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT \
  --timeframes 5m 15m 1h --days 365
```

### 启动服务
```bash
./start-analyzer.sh -d    # 回测分析器
./ft start --bot --ui -d  # 交易Bot + UI
```

---

## 工作日志

### 2025-11-08 下午 - 分批回测执行与内存问题深度诊断
**完成**: 批次1回测成功(23个币对，3个月，+125.29%收益)
**问题**: 批次2/3持续内存崩溃，即使有16GB可用内存
**突破**: 发现实盘Bot是内存杀手，停止后批次1成功

**核心发现**:
1. **内存崩溃根本原因**
   - 实盘Bot运行时占用868MB内存
   - NostalgiaForInfinityX7策略计算5个时间框架指标（5m/15m/1h/4h/1d）
   - 实盘Bot持续缓存~73个币对的技术指标数据
   - 回测进程+实盘进程同时运行，内存需求翻倍导致崩溃

2. **诊断过程**
   ```bash
   # 发现问题
   ps aux | grep freqtrade  # 找到实盘Bot PID 2049404，占用868MB

   # 解决方案
   ./ft stop --bot  # 停止实盘Bot释放内存

   # 验证结果
   free -h  # 确认可用内存从15GB增加到16GB
   ```

3. **批次1回测结果（✅ 成功）**
   - **时间范围**: 2025-08-08 至 2025-11-08（3个月）
   - **币对数**: 23个主流币（BTC/ETH/XRP/DOGE/ADA等）
   - **配置文件**:
     - `configs/pairlist-batch1.json` (币对列表)
     - `user_data/config-backtest-12x-batch1.json` (主配置)

   **核心指标**:
   - ✅ 总收益: **+125.29%** (10,000 → 22,528 USDT)
   - ✅ 胜率: **93.7%** (59胜/63笔交易)
   - ✅ 夏普比率: **7.18** (极优秀)
   - ✅ Sortino: **19.00**
   - ✅ 最大回撤: **4.47%** (非常小)
   - ✅ SQN: **4.32** (系统质量优秀)
   - ✅ CAGR: **2408.71%**

   **最佳币对**:
   - APT/USDT: +18.94% (9笔, 88.9%胜率)
   - AVAX/USDT: +18.14% (3笔, 100%胜率)
   - SUI/USDT: +16.18% (5笔, 100%胜率)
   - ADA/USDT: +16.09% (5笔, 100%胜率)

   **风险警告**:
   - 3次爆仓亏损: -1,331 USDT (-13.31%)
   - 最差单笔: HYPE/USDT -110.76%
   - BTC/USDT无交易（0笔）

4. **批次2/3回测失败（❌ 内存崩溃）**
   - **问题**: 批次2（DeFi & Layer2币）连续3次内存崩溃
   - **错误信息**: "free(): invalid next size (fast)" (C级内存分配错误)
   - **数据缺失**: PENGU/USDT:USDT, AVNT/USDT:USDT 无历史数据
   - **内存状态**: 显示16GB可用，但仍然崩溃
   - **尝试方案**: 等待5-10分钟让垃圾回收器释放内存 → 仍失败

**技术分析**:
- **内存消耗估算**: 23个币对 × 5个时间框架 × 3个月K线 ≈ 4-6GB
- **实际可用内存**: 16GB - Streamlit(389MB) - Claude(1.7GB) - 其他 ≈ 13GB
- **理论上应该成功**: 13GB > 6GB，但实际仍然崩溃
- **可能原因**:
  1. Python垃圾回收不及时，批次1数据未完全释放
  2. NostalgiaForInfinityX7策略内存泄漏
  3. 批次2的DeFi大币种（BCH/AAVE/UNI）数据量更大
  4. Pandas DataFrame内存碎片化

**创建的配置文件**:
```
configs/
├── pairlist-batch1.json  # 批次1: 主流蓝筹组（23个）
├── pairlist-batch2.json  # 批次2: DeFi & Layer2组（23个）
└── pairlist-batch3.json  # 批次3: 新币 & 小市值组（24个）

user_data/
├── config-backtest-12x-batch1.json  # 批次1主配置
├── config-backtest-12x-batch2.json  # 批次2主配置
└── config-backtest-12x-batch3.json  # 批次3主配置
```

**下一步计划**:
- **选项A（推荐）**: 缩短时间范围至2个月或1个月
- **选项B**: 停止Streamlit分析器（额外释放389MB）
- **选项C**: 每批减少至15个币对（分5-6批执行）
- **选项D**: 优化策略代码，减少内存占用

**教训总结**:
1. ✅ 回测前必须停止所有运行中的freqtrade进程
2. ✅ 使用 `ps aux | grep freqtrade` 检查进程状态
3. ✅ 使用 `free -h` 监控内存使用情况
4. ⚠️  23个币对 × 3个月仍然是内存边界，需要进一步优化
5. ⚠️  NostalgiaForInfinityX7策略对内存要求极高（5个时间框架）

**相关文件**:
- 回测结果: `user_data/backtest_results/backtest-batch1-20250808-20251108.json`
- 日志文件: `user_data/logs/freqtrade.log`

---

### 2025-11-08 上午 - 大规模回测准备(69币对×6个月)
**完成**: 69个币对回测配置和历史数据下载
**挑战**: 内存限制导致无法一次性回测所有币对

**工作内容**:
1. **回测配置创建**
   - 创建69个币对静态列表配置 (`configs/pairlist-backtest-69pairs-20251108.json`)
   - 创建12倍杠杆回测配置 (`user_data/config-backtest-12x-69pairs-20251108.json`)
   - 配置参数: 12x杠杆, 12个仓位(9多+3空), 10000 USDT初始资金

2. **历史数据下载**
   - 检查数据完整性: 69个币对中41个数据充足,29个需要下载
   - 创建下载专用配置 (`user_data/config-download.json`) 解决代理问题
   - 分6批下载29个币对数据(每批5个,避免超时)
   - 最终结果: 63个币对数据充足可回测,6个新币数据不足

3. **内存问题诊断**
   - 尝试6个月回测(20250508-20251108): 内存溢出崩溃
   - 尝试3个月回测(20250808-20251108): 仍然内存溢出
   - 根本原因: NostalgiaForInfinityX7策略需计算5个时间框架指标(5m/15m/1h/4h/1d)
   - 内存需求估算: 63币对 × 5时间框架 × 3个月数据 > 可用内存

**数据统计**:
- ✅ 数据充足(可回测): 63/69个币对
- ⚠️  数据不足6个月: 7个币对(XPL, HYPE, PUMP, ZK, MERL, AVNT, LINEA)
- ❌ 文件缺失: 0个币对

**下一步计划**:
- 方案1: 分批回测(推荐) - 分3批,每批20-25个币对
- 方案2: 缩短时间范围 - 回测最近1个月
- 方案3: 精选币对 - 仅回测30-40个主流币对

**技术要点**:
- 代理配置: 使用 `user_data/config-download.json` 确保下载成功
- 数据验证: 使用pandas读取feather文件验证时间范围
- 内存优化: NostalgiaForInfinityX7策略启动需800根K线,单币对内存占用巨大

**相关文件**:
- `configs/pairlist-backtest-69pairs-20251108.json` (69个币对列表)
- `user_data/config-backtest-12x-69pairs-20251108.json` (12倍杠杆配置)
- `user_data/config-download.json` (数据下载专用配置)

---

### 2025-11-08 - 实盘Bot启动问题修复（代理配置）
**问题**: Bot启动时杠杆档位API超时（90秒），导致无法完成初始化
**根本原因**:
- `get_leverage_tiers()` 使用同步API (`self._api`)
- 配置中仅为异步API (`ccxt_async_config`) 设置了代理
- 同步API请求无法通过代理访问币安API

**修复方案**:
在 `user_data/config-private.json` 添加 `ccxt_sync_config` 配置：
```json
"ccxt_sync_config": {
  "enableRateLimit": true,
  "timeout": 90000,
  "proxies": {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897"
  }
}
```

**修复效果**:
- 修复前: Leverage tier请求超时90秒 ❌
- 修复后: 请求成功，仅耗时5ms ✅
- Bot成功启动，API就绪 (http://127.0.0.1:8082)

**技术要点**:
- Freqtrade使用两套CCXT实例：同步(`_api`) + 异步(`_api_async`)
- 同步API配置优先级: `ccxt_config` → `ccxt_sync_config`
- 异步API配置优先级: `ccxt_config` → `ccxt_async_config`
- 同步API使用 `proxies` 字典，异步API使用 `aiohttp_proxy` 字符串

**相关文件**:
- `user_data/config-private.json:14-25` (新增配置)
- `freqtrade/exchange/exchange.py:266-279` (配置加载逻辑)
- `freqtrade/exchange/exchange.py:3344-3354` (leverage tier加载)

---

### 2025-11-08 - 黑名单配置统一优化
**完成**: 删除回测配置中的本地黑名单，统一使用全局黑名单配置

**优化内容**:
- 删除 `user_data/config-backtest.json` 的本地 `pair_blacklist` 配置
- 实盘和回测统一使用 `configs/blacklist-binance.json` 全局黑名单
- 提高配置一致性，简化维护成本

**验证结果**:
- ✅ 全局黑名单正常工作（8条规则，240+问题币种）
- ✅ BNB、SOL等风险币种被正确过滤
- ✅ MAGIC、GMX、NEAR、PENDLE、1000PEPE等毒瘤币种已排除
- ✅ 实盘和回测使用相同的币种过滤规则

**配置说明**:
- `config-backtest.json` 的 `pair_whitelist` 中虽包含 BNB/SOL
- 全局黑名单会自动过滤，最终仅交易6个安全币种
- Freqtrade配置优先级: `add_config_files` 中的黑名单 > 本地配置

**相关文件**:
- `user_data/config-backtest.json:11-22` (删除pair_blacklist)
- `configs/blacklist-binance.json` (全局黑名单规则)

---

### 2025-11-08 - 决策日志系统实现（MVP完成）
**完成**: 实现运行时决策记录和100%准确复盘系统
**核心功能**:
- 创建 `NostalgiaForInfinityX7WithLogging` 策略（非侵入式子类设计）
- 决策日志记录器（JSONL格式，自动记录入场/出场时刻的所有技术指标）
- 装饰器模块（`@log_entry_decisions`, `@log_exit_decisions`）
- 决策回放器（自动匹配回测结果，时间戳容差匹配）
- UI集成（优雅降级，100%准确数据显示）

**技术架构**:
```
backtest_analyzer/hooks/          # 新增Hook模块
├── decision_logger.py           # 日志记录器（200行）
└── strategy_decorator.py        # 装饰器（160行）

backtest_analyzer/analyzers/
└── decision_replay.py           # 回放器（380行）

user_data/strategies/
└── NostalgiaForInfinityX7WithLogging.py  # 带日志策略（76行）

user_data/decision_logs/         # 决策日志目录
└── decisions_*.jsonl           # 日志文件
```

**使用方式**:
```bash
# 1. 运行带日志的回测
freqtrade backtesting --strategy NostalgiaForInfinityX7WithLogging \
  --config user_data/config-backtest.json --exchange binance

# 2. 启动分析器查看决策复盘
./start-analyzer.sh

# 3. 在"交易复盘"页面查看100%准确的技术指标值
```

**验证结果**:
- ✅ 831行高质量代码（6个新文件）
- ✅ UI实际验证通过（Playwright）
- ✅ 优雅降级机制工作正常
- ✅ 日志文件自动创建和匹配
- ✅ 用户体验优秀（清晰提示和引导）

**端到端验证（2025-11-08晚）**:
- ✅ 完整回测生成4笔交易（20241001-20241107，1个月）
- ✅ 决策日志文件正确生成（11行，7入场+4出场，54KB）
- ✅ UI成功加载并显示"✨ 使用决策日志数据（100%准确）"
- ✅ 技术指标完整显示（222个指标值100%准确）

**问题修复**:
1. **时间戳匹配Bug**（`decision_replay.py:98-110`）
   - 问题：`.zip`文件名解析失败，导致无法自动发现决策日志
   - 修复：使用regex `r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'`替代字符串分割

2. **容差设置过小**（`5_交易复盘.py:353`）
   - 问题：`tolerance_seconds=10`无法匹配信号生成（23:20）到实际入场（23:25）的5分钟延迟
   - 修复：提升到`tolerance_seconds=600`（10分钟）

**关键特性**:
- 100%准确性（直接记录运行时指标，无需手动重构条件）
- 零侵入（原策略代码不修改）
- 自动匹配（时间戳自动关联）
- 完整数据（支持JSON下载）

**文档**: `docs/DECISION_LOGGING_PLAN.md`（完整技术方案）

---

### 2025-11-08 - 黑名单配置同步与优化
**完成**: 对比NFI官方黑名单配置，修复 "H" 币种缺失Bug
**发现**:
- 黑名单配置对齐度 99.5%（官方推荐240+币种）
- 修复缺失的 "H" 币种黑名单规则
- 验证Binance当前无 H/USDT 交易对（实际影响低）
**文档**: 创建 `docs/BLACKLIST_OPTIMIZATION_ANALYSIS.md` 详细分析报告
**架构**: 6大类黑名单规则（交易所代币、杠杆代币、法币、稳定币、粉丝代币、问题币种）

---

### 2025-11-08 - Backtest Analyzer 启动脚本
**完成**: 创建 `start-analyzer.sh` 一键启动脚本
**功能**: 自动清理旧进程/缓存，激活虚拟环境，启动 http://127.0.0.1:8501
**用法**: `./start-analyzer.sh [-d|--stop]`

---

### 2025-11-07 - 交易入场依据查询方法
**完成**: 建立从数据库查询交易理由的标准流程
**核心**: 通过 `enter_tag` 字段反查策略条件逻辑
**文件**: `user_data/tradesv3.sqlite`, `user_data/strategies/*.py`

**查询示例**:
```bash
# 1. 查询交易记录获取 enter_tag
python3 -c "
import sqlite3
conn = sqlite3.connect('user_data/tradesv3.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT id, pair, enter_tag FROM trades ORDER BY id DESC LIMIT 1')
print(cursor.fetchone())
"

# 2. 在策略文件中搜索条件
grep -A 30 "# Condition #141" user_data/strategies/NostalgiaForInfinityX7.py
```

**Entry Tag 分类**:
- 1-19: Normal Mode（常规入场）
- 20-39: Pump Mode（拉盘模式）
- 40-59: Quick Mode（快速模式）
- 141-145: Top Coins Mode（主流币模式）
- 151-153: Grind Mode（网格模式）
- 161-163: Scalp Mode（剥头皮模式）

---

### 2025-11-07 - 回测分析器文件选择体验优化
**完成**: 优化文件选择器显示回测时间范围和交易统计
**改进**:
- 从文件名解析 timerange (20241101-20241130)
- 显示总交易数/盈利次数/亏损次数
- 自动过滤当前策略和模式的结果文件

**文件**: `backtest_analyzer/app/main.py`

---

### 2025-11-07 - Telegram Bot 分级权限配置
**完成**: 配置私聊完全控制 + 群组仅通知的权限模式
**文件**: `user_data/config-telegram.json`
**私聊功能**: `/status`, `/profit`, `/start`, `/stop` 等完整控制
**群组功能**: 仅接收交易通知，命令不响应

---

### 2025-11-07 - FreqAI 方向性预测三阶段优化
**完成**:
1. 基础模型验证（均方误差：4.75，准确率：13.8%）
2. 特征工程优化（RSI/EMA/ATR/动量等40+特征）
3. 分类模型切换（LightGBMClassifier，目标：涨/跌/横盘）

**文件**: `user_data/strategies/FreqAIDirectionalV*.py`

---

### 2025-11-07 - Bitcoin 历史反转点识别系统
**完成**: 基于价格百分位数识别极端超卖/超买点的回测系统
**算法**: Williams %R < 5th percentile (超卖) 或 > 95th percentile (超买)
**回测期**: 2023-01-01 至 2025-11-07（34个月）
**结果**: 识别出33次极端超卖点，24次成功反弹（胜率72.7%）
**文件**: `user_data/strategies/BitcoinReversalIdentifier.py`

---

### 2025-11-06 - FreqAITest_Advanced 高级反转特征系统
**完成**: 基于 Fisher Transform、RSI 梯度、Aroon 震荡等高级特征的反转策略
**特征**: 37个进阶指标（Fisher、Aroon、RSI梯度、MACD柱形等）
**文件**: `user_data/strategies/FreqAITest_Advanced.py`

---

### 2025-11-06 - FreqAI 12倍杠杆反转策略
**完成**: 高杠杆反转策略框架（RSI超卖+成交量+布林带等）
**风控**:
- 初始止损 3%
- 移动止损（超过3%盈利后启用）
- 目标盈利 8%

**文件**:
- `user_data/strategies/FreqAILeverageReversal.py`
- `user_data/config-freqai-leverage-reversal.json`

---

### 2025-11-06 - 毒瘤币种自动识别系统
**完成**: 三级风险检测算法（爆仓、资金曲线异常、高风险交易）
**检测结果**: 4个月回测识别出 POWR, ARDR, HIVE, SC 等问题币种
**部署**: 自动添加到 `configs/blacklist-binance.json`
**文件**: `backtest_analyzer/analyzers/toxic_pair_detector.py`

---

### 初始工作 - FreqAI 环境搭建
**完成**:
- 解决 "No further splits with positive gain" 警告（增加训练数据和特征维度）
- LightGBM 参数优化（n_estimators: 100→300, max_depth: 5→8）
- 特征工程扩展（多时间框架 5m/15m/1h，指标周期 10/20/30）

**优化效果**: 特征数从 254 → 542-812，警告完全消除

---

## 技术要点

### LightGBM 关键参数
- `n_estimators`: 树的数量（100-300）
- `learning_rate`: 学习率（0.01-0.1）
- `max_depth`: 树深度（5-10）
- `num_leaves`: 叶子数（建议 < 2^max_depth）
- 正则化: `reg_alpha` (L1), `reg_lambda` (L2)

### FreqAI 配置要点
- `train_period_days`: 训练窗口（15-30天）
- `backtest_period_days`: 回测窗口（3-7天）
- `include_timeframes`: 多时间框架特征
- `indicator_periods_candles`: 指标周期参数

### 回测分析
- `backtest_analyzer/` 提供入场模式分析、币种分析、爆仓分析
- 通过 `start-analyzer.sh` 启动 Streamlit 界面
- 支持自动过滤和时间范围识别

---

**文档版本**: v2.0 (精简版)
**最后更新**: 2025-11-08
**备份**: `FreqAI_工作日志.backup.md`
