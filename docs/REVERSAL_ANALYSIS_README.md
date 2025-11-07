# 加密货币反转点识别和可视化系统

## 概述

这是一个专业的加密货币价格反转点识别和可视化工具，用于在历史K线数据中自动识别重要的价格反转点（顶部和底部），并通过交互式网页界面展示结果。

**⚠️ 前瞻偏差警告：** 此工具使用未来数据来标记历史反转点，仅适用于：
1. 创建机器学习训练数据集
2. 历史市场行为分析
3. 策略回测研究

**不可直接用于实盘交易！**

## 特性

### 三种反转识别方法

1. **固定阈值方法 (Fixed Threshold)**
   - 向前看固定时间窗口（默认6小时）
   - 使用固定百分比阈值（默认3%）
   - 最简单直接，适合快速探索

2. **自适应阈值方法 (Adaptive Threshold)**
   - 基于历史波动性（ATR）动态调整阈值
   - 高波动期提高阈值，低波动期降低阈值
   - 更适应不同市场环境

3. **局部极值方法 (Local Extreme)**
   - 识别摆动高点和摆动低点（swing high/low）
   - 验证极值点后确实发生反转
   - 最精细，识别的反转点最少但质量最高

### 交互式可视化

- **K线图**: 专业的红绿K线图
- **成交量**: 柱状图显示成交量
- **反转标记**:
  - 红色向下三角形 (▼) = 顶部反转
  - 绿色向上三角形 (▲) = 底部反转
- **悬停信息**: 详细的反转点信息
- **时间选择器**: 快速切换时间范围（1周/1月/3月/6月/1年/全部）
- **统计面板**: 完整的统计分析数据
- **反转列表**: 可排序的反转点表格

### 输出格式

- **HTML文件**: 交互式可视化，可在浏览器中打开
- **CSV文件**: 反转点数据，可用于进一步分析
- **文本报告**: 详细的统计分析报告

## 安装

确保已安装Freqtrade及其依赖：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 依赖已在Freqtrade安装时包含
# pandas, numpy, plotly等
```

## 快速开始

### 1. 准备数据

首先下载历史数据（使用期货数据格式）：

```bash
# 设置代理（如果需要）
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

# 下载BTC期货数据
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT:USDT \
  --timeframes 5m \
  --days 90 \
  --trading-mode futures
```

### 2. 基础用法

分析BTC最近3个月数据（使用默认激进参数）：

```bash
python scripts/analyze_reversals.py --pairs BTC/USDT:USDT
```

### 3. 查看结果

脚本会输出类似信息：

```
分析完成！
  处理的交易对: 1
  使用的方法: fixed, adaptive, extreme
  输出目录: user_data/reversal_results

打开HTML文件即可查看交互式可视化结果。
```

在浏览器中打开生成的HTML文件，例如：
```bash
# Linux
xdg-open user_data/reversal_results/BTC_USDT:USDT_fixed_*.html

# macOS
open user_data/reversal_results/BTC_USDT:USDT_fixed_*.html

# Windows
start user_data/reversal_results/BTC_USDT:USDT_fixed_*.html
```

## 高级用法

### 分析多个交易对

```bash
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT ETH/USDT:USDT BNB/USDT:USDT \
  --methods all
```

### 指定时间范围

```bash
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --timerange 20240101-20241231
```

### 只使用特定方法

```bash
# 只使用固定阈值方法
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --methods fixed

# 使用固定阈值和自适应方法
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --methods fixed adaptive
```

### 分析现货数据

```bash
python scripts/analyze_reversals.py \
  --pairs BTC/USDT \
  --candle-type spot
```

### 使用自定义配置

```bash
python scripts/analyze_reversals.py \
  --config user_data/reversal_config.json
```

## 配置文件

配置文件位于 `user_data/reversal_config.json`，可以调整以下参数：

### 检测器参数

```json
{
  "detectors": {
    "fixed": {
      "forward_window_hours": 6,    // 向前看的时间窗口
      "threshold_pct": 3.0           // 反转阈值百分比
    },
    "adaptive": {
      "forward_window_hours": 6,
      "volatility_window_days": 30,  // 计算波动性的窗口
      "threshold_multiplier": 2.0    // 波动性倍数
    },
    "extreme": {
      "swing_window": 5,              // 摆动点窗口
      "confirmation_threshold_pct": 3.0,
      "forward_window_hours": 6
    }
  }
}
```

### 参数调整建议

**固定阈值方法：**
- **保守**: `forward_window_hours=24, threshold_pct=8.0`
- **中等**: `forward_window_hours=12, threshold_pct=5.0`
- **激进**: `forward_window_hours=6, threshold_pct=3.0` (默认)

**自适应阈值方法：**
- `threshold_multiplier`: 建议范围 1.5-3.0
- 数值越大，识别的反转点越少但质量越高

**局部极值方法：**
- `swing_window`: 建议范围 3-10
- 数值越大，识别的摆动点越少但越显著

## 文件结构

```
scripts/
├── analyze_reversals.py                    # 主入口脚本
└── reversal_analysis/                      # 分析模块包
    ├── __init__.py                         # 包初始化
    ├── detectors.py                        # 三种反转识别器
    ├── visualizer.py                       # Plotly可视化
    └── statistics.py                       # 统计分析

user_data/
├── reversal_config.json                    # 配置文件
└── reversal_results/                       # 输出目录
    ├── BTC_USDT:USDT_fixed_*.html         # HTML可视化
    ├── BTC_USDT:USDT_fixed_*.csv          # CSV数据
    └── ...
```

## 输出文件说明

### HTML文件

交互式可视化文件，包含：
- K线图和成交量
- 反转点标记
- 统计面板
- 反转列表表格
- 时间范围选择器

### CSV文件

包含以下列：
- `date`: 时间戳
- `open`, `high`, `low`, `close`, `volume`: OHLCV数据
- `reversal_type`: 'top' 或 'bottom'
- `reversal_magnitude`: 反转幅度（百分比）
- `forward_return`: 实际收益率
- `confidence`: 置信度 (0-1)
- `detector_name`: 使用的检测方法

## 使用场景示例

### 场景1：创建ML训练数据集

```bash
# 下载长期历史数据
freqtrade download-data \
  --exchange binance \
  --pairs BTC/USDT:USDT \
  --timeframes 5m \
  --days 365 \
  --trading-mode futures

# 识别反转点
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --methods adaptive \
  --timerange 20230101-20241231

# 使用生成的CSV文件训练模型
```

### 场景2：不同方法对比

```bash
# 运行所有方法
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --methods all

# 对比三个HTML文件，了解不同方法的特点
```

### 场景3：多交易对分析

```bash
# 批量分析多个交易对
python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT ETH/USDT:USDT BNB/USDT:USDT SOL/USDT:USDT \
  --methods fixed

# 对比不同加密货币的反转模式
```

## 常见问题

### Q: 为什么没有发现反转点？

A: 可能的原因：
1. 时间范围太短，市场波动不够大
2. 阈值设置过高（降低 `threshold_pct`）
3. 向前看窗口太长（减少 `forward_window_hours`）

### Q: 为什么识别出很多反转点？

A: 可能的原因：
1. 使用了自适应方法且市场高度波动
2. 阈值设置过低（提高 `threshold_pct`）
3. 向前看窗口太短（增加 `forward_window_hours`）

### Q: 哪种方法最好？

A: 取决于用途：
- **固定阈值**: 简单直接，适合快速探索
- **自适应阈值**: 更多反转点，适合收集大量训练数据
- **局部极值**: 更少但更高质量，适合关键反转点研究

建议：先用所有方法运行一次，对比结果后选择最适合你需求的方法。

### Q: 如何处理期货和现货的交易对格式？

A:
- **期货**: 使用格式 `BTC/USDT:USDT`，文件名为 `BTC_USDT_USDT-5m-futures.feather`
- **现货**: 使用格式 `BTC/USDT`，文件名为 `BTC_USDT-5m.feather`
- 使用 `--candle-type` 参数指定类型

### Q: 可以用于实盘交易吗？

A: **不可以！** 这个工具使用前瞻数据（向前看未来价格），存在严重的前瞻偏差。它只能用于：
- 创建历史数据集
- 研究历史模式
- 训练机器学习模型

如果要用于实盘，需要完全重新设计检测逻辑，只使用当前和历史数据。

## 技术细节

### 性能优化

- 使用Pandas向量化操作，避免循环
- 自动处理大数据集
- 高效的rolling计算

### 数据边界处理

- 数据开头：无法完整计算历史波动性的部分被标记为无效
- 数据结尾：无法向前看的部分被标记为无效
- 保证所有反转点都有完整的前后数据支持

### 前瞻偏差

代码中包含明确的警告注释：

```python
# ⚠️ FORWARD-LOOKING: Calculate future price extremes
# This is only suitable for historical analysis and training data creation
```

所有使用未来数据的地方都有清晰标注。

## 贡献

欢迎贡献新的检测方法或改进现有功能！

可能的扩展方向：
- 添加更多技术指标支持
- 实现机器学习预测模型
- 添加更多可视化选项
- 支持多时间框架分析

## 许可

本工具是Freqtrade项目的一部分，遵循相同的开源许可。

## 联系

如有问题或建议，请在Freqtrade GitHub仓库提交issue。

---

**最后提醒：此工具仅用于研究和学习，不提供任何投资建议。加密货币交易存在高风险，请谨慎决策。**
