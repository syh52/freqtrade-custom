# 📊 Freqtrade 回测结果深度分析管线

专为 **NostalgiaForInfinityX7** 策略设计的回测结果分析系统，提供交易深度复盘、爆仓诊断、币种筛选等功能。

## 🎯 核心功能

### 1. 🔴 爆仓问题诊断
- 识别24笔爆仓的共性原因
- 分析高风险币种和入场模式
- DCA/加仓行为对爆仓的影响分析
- 生成预防措施和黑名单配置

### 2. 🔬 交易深度复盘（核心创新）
针对每笔差交易提供：
- **K线级别分析**：结合实际K线数据和技术指标
- **最优点搜索**：自动找出最优入场/出场时机
- **反事实分析**：如果在最优点交易会怎样？
- **拒绝信号分析**：检查同时段被拒绝的信号（机会成本）
- **反思报告**：为什么这笔交易不理想？如何改进？

### 3. 📈 多维度分析
- 17种入场模式效果对比
- 币种表现排行和毒瘤币检测
- 时间维度分析（日/周/月/小时）
- Grind模式专项分析

## 🏗️ 项目结构

```
backtest_analyzer/
├── core/                          # 核心数据处理
│   ├── loader.py                  # 回测结果加载（复用Freqtrade API）
│   ├── data_fetcher.py           # K线数据获取
│   ├── strategy_runner.py        # 策略指标重算
│   └── cleaner.py                # 数据清洗和特征工程
├── analyzers/                     # 分析模块
│   ├── liquidation_analyzer.py   # 爆仓专项分析
│   ├── trade_replay.py          # 交易深度复盘引擎 ⭐
│   ├── toxic_pair_detector.py    # 币种筛选（待实现）
│   └── entry_mode_analyzer.py    # 入场模式分析（待实现）
├── visualizers/                   # 可视化组件
│   ├── kline_chart.py            # K线图（Plotly）
│   └── dashboard_components.py   # 仪表盘组件（待实现）
├── app/                           # Streamlit Web应用
│   ├── main.py                   # 主入口
│   └── pages/
│       └── 5_交易复盘.py          # 交易复盘页面 ⭐
└── scripts/                       # 工具脚本（待实现）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd backtest_analyzer

# 安装依赖（确保已激活freqtrade虚拟环境）
source ../.venv/bin/activate
pip install -r requirements.txt
```

### 2. 准备回测结果

确保您已经运行了回测，结果保存在 `user_data/backtest_results/` 目录下。

示例：
```bash
# 运行回测
freqtrade backtesting \
  --config user_data/config-custom.json \
  --config user_data/config-private.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20250201-20250930
```

### 3. 启动Web应用

```bash
# 从项目根目录启动
streamlit run backtest_analyzer/app/main.py
```

应用将在浏览器中打开（默认 http://localhost:8501）

### 4. 使用分析功能

1. **加载数据**：在左侧边栏输入回测文件路径，点击"加载数据"
2. **查看总览**：主页显示关键指标和快速洞察
3. **深度复盘**：导航到"交易复盘"页面，选择需要分析的交易

## 📖 使用示例

### 示例1: 分析爆仓交易

```python
from backtest_analyzer.core.loader import BacktestResultLoader
from backtest_analyzer.core.cleaner import DataCleaner
from backtest_analyzer.analyzers.liquidation_analyzer import LiquidationAnalyzer

# 加载数据
loader = BacktestResultLoader("user_data/backtest_results/backtest-result-2025-11-07_16-36-54.json")
data = loader.load_all()

# 数据增强
trades_df = DataCleaner.clean_and_enhance_trades(data['trades'])

# 爆仓分析
analyzer = LiquidationAnalyzer(trades_df)
analysis = analyzer.analyze()

# 查看结果
print(f"爆仓数量: {analysis['summary']['liquidation_count']}")
print(f"高风险币种:\n{analysis['risk_pairs']}")
print(f"预防建议:\n{analysis['recommendations']}")
```

### 示例2: 复盘单笔交易

```python
from backtest_analyzer.core.data_fetcher import DataFetcher
from backtest_analyzer.core.strategy_runner import StrategyRunner
from backtest_analyzer.analyzers.trade_replay import TradeReplayEngine

# 选择一笔交易
trade = trades_df.iloc[0]

# 获取K线数据
fetcher = DataFetcher()
candles_df = fetcher.get_data_for_trade(
    pair=trade['pair'],
    open_date=trade['open_date'],
    close_date=trade['close_date'],
    expand_candles=100
)

# 重新计算技术指标
runner = StrategyRunner(strategy_name="NostalgiaForInfinityX7")
indicators_df = runner.populate_indicators(candles_df, {'pair': trade['pair']})

# 执行复盘
engine = TradeReplayEngine(trade, candles_df, indicators_df)
analysis = engine.analyze()

# 查看最优点
print(f"最优入场点: {analysis['optimal_points']['entry']}")
print(f"最优出场点: {analysis['optimal_points']['exit']}")
print(f"反思: {analysis['reflection']}")
```

## 🔧 配置说明

### 数据位置

默认情况下，系统会从以下位置查找数据：

- **回测结果**: `user_data/backtest_results/`
- **K线数据**: `user_data/data/binance/`
- **配置文件**: `user_data/config-custom.json` + `user_data/config-private.json`
- **策略文件**: `user_data/strategies/NostalgiaForInfinityX7.py`

### K线数据准备

如果分析时提示缺少K线数据，使用以下命令下载：

```bash
# 设置代理（本项目需要）
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

# 下载数据
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \  # 替换为您需要的币种
  --timeframes 5m \
  --days 365 \
  --dataformat-ohlcv feather
```

## 📊 输出说明

### 爆仓分析输出

- **风险币种列表**：按风险评分排序，标注风险等级（🟡🟠🔴）
- **风险模式**：识别容易爆仓的入场模式
- **预防建议**：包含优先级、类型、具体行动
- **黑名单配置**：自动生成的 `blacklist-dynamic.json`

### 交易复盘输出

对每笔交易提供：

1. **K线图**：
   - 实际入场点（绿色箭头）
   - 最优入场点（蓝色虚线箭头）
   - 实际出场点（红色箭头）
   - 最优出场点（橙色虚线箭头）
   - 技术指标叠加（EMA, RSI等）

2. **问题诊断**：
   - 入场时机问题（如RSI超买/超卖）
   - 出场时机问题（过早/过晚）
   - 盈利效率分析（MFE vs 实际收益）

3. **改进建议**：
   - 针对性的策略优化建议
   - 参数调整方向
   - 风险控制措施

4. **反事实分析**：
   - 理论最优收益是多少？
   - 与实际收益的差距在哪里？
   - 如何缩小这个差距？

## 🎓 进阶使用

### 自定义分析

您可以继承基类实现自定义分析器：

```python
from backtest_analyzer.analyzers.trade_replay import TradeReplayEngine

class MyCustomAnalyzer(TradeReplayEngine):
    def _assess_entry_conditions(self, candle):
        # 添加自定义的入场条件评估
        issues = super()._assess_entry_conditions(candle)

        # 您的自定义逻辑
        if candle.get('custom_indicator', 0) > threshold:
            issues.append("⚠️ 自定义指标异常")

        return issues
```

### 批量分析

```python
# 批量复盘所有亏损交易
losing_trades = trades_df[trades_df['profit_ratio'] < 0]

for idx, trade in losing_trades.iterrows():
    print(f"\n=== 交易 #{idx} ===")
    # 执行复盘...
    analysis = replay_trade(trade, candles_df, indicators_df)
    print(analysis['reflection'])
```

## 🐛 故障排除

### 问题1: 提示"未找到K线数据"

**解决方案**：
1. 确认数据目录结构正确：`user_data/data/binance/`
2. 使用 `freqtrade download-data` 下载缺失的数据
3. 检查文件格式（推荐使用feather格式）

### 问题2: 策略加载失败

**解决方案**：
1. 确认策略文件在 `user_data/strategies/` 目录
2. 检查策略名称是否与文件名一致
3. 确保策略没有语法错误

### 问题3: Streamlit启动失败

**解决方案**：
```bash
# 确认已安装streamlit
pip install streamlit

# 从项目根目录启动
cd /home/dministrator/Newproject/freqtrade
streamlit run backtest_analyzer/app/main.py
```

## 🔮 未来功能规划

**已实现** ✅：
- [x] 核心数据加载模块
- [x] 爆仓分析器
- [x] 交易复盘引擎
- [x] K线可视化
- [x] Streamlit Web应用

**待实现** 🚧：
- [ ] 毒瘤币检测器（扩展现有脚本）
- [ ] 入场模式分析器
- [ ] 拒绝信号分析器
- [ ] 其他Streamlit页面（总览、爆仓、币种、入场模式）
- [ ] 命令行批量分析脚本
- [ ] PDF报告导出
- [ ] 参数敏感性分析
- [ ] A/B测试框架

## 📝 技术栈

- **后端**: Python 3.9+
- **数据处理**: pandas, numpy
- **可视化**: Plotly, Streamlit
- **Freqtrade**: 复用官方API和策略接口
- **分析**: scipy, scikit-learn

## 🤝 贡献

欢迎贡献代码、报告问题或提出功能建议！

## 📄 许可证

本项目遵循与Freqtrade相同的许可协议（MIT License）

---

**作者**: 由 Claude Code 设计
**版本**: v1.0
**最后更新**: 2025-11-07

💡 **提示**: 建议先分析爆仓交易和差交易，这些是最有价值的改进点！
