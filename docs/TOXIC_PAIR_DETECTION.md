# 毒瘤币种实时识别系统

## 核心问题

动态交易对列表（VolumePairList）会不断引入新币种，如何在**事前**识别潜在的"毒瘤币种"（如INJ、CRV），避免深套？

---

## 🔬 毒瘤币种的DNA特征

### 案例分析：INJ vs LINK

| 特征 | INJ（毒瘤） | LINK（健康） | 关键差异 |
|------|-------------|--------------|----------|
| **Grind持仓时间** | 14天 | 5.2天 | 持仓长度本身不是问题 |
| **Grind最终收益** | **-9,054 USDT** | **+2,549 USDT** | 收益是关键 |
| **爆仓记录** | **有** | 无 | 致命信号 |
| **强制平仓** | **有** | 无 | 致命信号 |
| **最大单笔亏损** | **-10,543 USDT** | -794 USDT | 极端亏损 |
| **整体胜率** | 70% | 85.7% | 相对健康 |

**核心发现：**
- ❌ **错误指标**：持仓时间长（LINK也很长，但盈利）
- ✅ **正确指标**：爆仓、极端亏损、长期持仓且亏损

---

## 🎯 三级识别体系

### Level 1: 🔴 致命信号（立即拉黑）

满足**任一条件**即为高危毒瘤：

```python
def is_deadly_toxic(pair_stats):
    """致命毒瘤：立即加入黑名单"""

    # 信号1: 有爆仓记录
    if pair_stats['has_liquidation']:
        return True, "爆仓记录"

    # 信号2: 长期深套（持仓>7天且Grind亏损>3000 USDT）
    if (pair_stats['grind_avg_duration'] > 168 and
        pair_stats['grind_profit'] < -3000):
        return True, f"长期深套（{pair_stats['grind_avg_duration']/24:.1f}天，亏损{pair_stats['grind_profit']:.0f}U）"

    # 信号3: 极端单笔亏损（单笔亏损>5000 USDT）
    if pair_stats['max_single_loss'] < -5000:
        return True, f"极端亏损（{pair_stats['max_single_loss']:.0f}U）"

    # 信号4: 强制平仓且巨额亏损
    if (pair_stats['has_force_exit'] and
        pair_stats['grind_profit'] < -2000):
        return True, f"强制平仓且亏损{pair_stats['grind_profit']:.0f}U"

    return False, None
```

**当前案例：INJ满足多条**
- ✅ 有爆仓记录
- ✅ 长期深套（14天，-9,054 USDT）
- ✅ 极端亏损（-10,543 USDT）
- ✅ 强制平仓且巨额亏损

---

### Level 2: ⚠️ 警告信号（限制Grind）

满足**2+条件**为中等风险：

```python
def is_warning_toxic(pair_stats):
    """警告级别：禁用Grind模式，但允许普通交易"""

    risk_signals = []

    # 信号1: 整体胜率较低
    if pair_stats['win_rate'] < 70:
        risk_signals.append("胜率低于70%")

    # 信号2: Grind表现差
    if (pair_stats['grind_trades'] >= 2 and
        pair_stats['grind_win_rate'] < 70):
        risk_signals.append("Grind胜率差")

    # 信号3: 有较大单笔亏损
    if pair_stats['max_single_loss'] < -1000:
        risk_signals.append(f"单笔亏损{pair_stats['max_single_loss']:.0f}U")

    # 信号4: Grind持仓过长但整体亏损
    if (pair_stats['grind_avg_duration'] > 120 and  # 5天
        pair_stats['grind_profit'] < 0):
        risk_signals.append(f"长期持仓但亏损")

    # 信号5: 频繁止损
    if pair_stats.get('stoploss_count', 0) >= 2:
        risk_signals.append("频繁止损")

    if len(risk_signals) >= 2:
        return True, risk_signals

    return False, []
```

**当前案例：CRV满足**
- ✅ 有爆仓记录（虽然是Level 1，但整体还盈利）
- ✅ 单笔亏损-1,164 USDT

---

### Level 3: ✅ 健康币种（正常使用Grind）

不满足上述条件的币种，正常使用Grind模式。

**特征：**
- 无爆仓记录
- Grind胜率>80%或整体盈利
- 单笔最大亏损<-1000 USDT

---

## 🤖 实时监控系统设计

### 方案1: 回测定期分析（推荐起步）

**原理：** 每周用最近1-3个月数据回测，自动生成黑名单

```bash
#!/bin/bash
# scripts/detect_toxic_pairs.sh

# 1. 运行回测
freqtrade backtesting \
  --config user_data/config-backtest-realistic.json \
  --timerange $(date -d '3 months ago' +%Y%m%d)-$(date +%Y%m%d) \
  --export trades

# 2. 分析结果，生成黑名单
python3 scripts/analyze_toxic_pairs.py

# 3. 自动更新配置
# 输出: user_data/blacklist_auto_generated.json
```

**Python分析脚本：**

```python
#!/usr/bin/env python3
# scripts/analyze_toxic_pairs.py

import json
import pandas as pd
from pathlib import Path

def analyze_toxic_pairs(backtest_result_path):
    """分析回测结果，识别毒瘤币种"""

    # 读取回测数据
    with open(backtest_result_path) as f:
        data = json.load(f)

    strategy_name = list(data['strategy'].keys())[0]
    trades = pd.DataFrame(data['strategy'][strategy_name]['trades'])

    # 计算每个币种的统计数据
    toxic_pairs = []
    warning_pairs = []

    for pair in trades['pair'].unique():
        pair_trades = trades[trades['pair'] == pair]
        grind_trades = pair_trades[pair_trades['enter_tag'].str.contains('120', na=False)]

        stats = {
            'pair': pair,
            'total_trades': len(pair_trades),
            'total_profit': pair_trades['profit_abs'].sum(),
            'win_rate': len(pair_trades[pair_trades['profit_abs'] > 0]) / len(pair_trades) * 100,
            'max_single_loss': pair_trades['profit_abs'].min(),
            'has_liquidation': 'liquidation' in pair_trades['exit_reason'].values,
            'has_force_exit': 'force_exit' in pair_trades['exit_reason'].values,
        }

        if len(grind_trades) > 0:
            stats.update({
                'grind_trades': len(grind_trades),
                'grind_profit': grind_trades['profit_abs'].sum(),
                'grind_avg_duration': grind_trades['duration_hours'].mean(),
                'grind_win_rate': len(grind_trades[grind_trades['profit_abs'] > 0]) / len(grind_trades) * 100,
            })

        # 应用识别规则
        is_deadly, reason = is_deadly_toxic(stats)
        if is_deadly:
            toxic_pairs.append({'pair': pair, 'reason': reason, 'stats': stats})
            continue

        is_warning, signals = is_warning_toxic(stats)
        if is_warning:
            warning_pairs.append({'pair': pair, 'signals': signals, 'stats': stats})

    # 生成黑名单配置
    blacklist = {
        'pair_blacklist': [p['pair'] for p in toxic_pairs],
        'grind_blacklist': [p['pair'] for p in warning_pairs],
        'generated_at': datetime.now().isoformat(),
        'details': {
            'toxic_pairs': toxic_pairs,
            'warning_pairs': warning_pairs
        }
    }

    # 保存结果
    with open('user_data/blacklist_auto_generated.json', 'w') as f:
        json.dump(blacklist, f, indent=2)

    print(f"✅ 检测完成")
    print(f"   致命毒瘤: {len(toxic_pairs)}个")
    print(f"   警告币种: {len(warning_pairs)}个")

    return blacklist

def is_deadly_toxic(stats):
    """Level 1: 致命信号检测"""
    if stats.get('has_liquidation'):
        return True, "爆仓记录"

    if (stats.get('grind_avg_duration', 0) > 168 and
        stats.get('grind_profit', 0) < -3000):
        return True, f"长期深套"

    if stats['max_single_loss'] < -5000:
        return True, f"极端亏损"

    if (stats.get('has_force_exit') and
        stats.get('grind_profit', 0) < -2000):
        return True, f"强制平仓巨额亏损"

    return False, None

def is_warning_toxic(stats):
    """Level 2: 警告信号检测"""
    signals = []

    if stats['win_rate'] < 70:
        signals.append("低胜率")

    if (stats.get('grind_trades', 0) >= 2 and
        stats.get('grind_win_rate', 100) < 70):
        signals.append("Grind表现差")

    if stats['max_single_loss'] < -1000:
        signals.append("大额亏损")

    if (stats.get('grind_avg_duration', 0) > 120 and
        stats.get('grind_profit', 0) < 0):
        signals.append("长期持仓亏损")

    return len(signals) >= 2, signals

if __name__ == '__main__':
    # 查找最新回测结果
    results_dir = Path('user_data/backtest_results')
    latest = max(results_dir.glob('*.json'), key=lambda p: p.stat().st_mtime)

    analyze_toxic_pairs(latest)
```

**使用流程：**

```bash
# 1. 首次运行：分析历史回测
./scripts/detect_toxic_pairs.sh

# 2. 查看结果
cat user_data/blacklist_auto_generated.json

# 3. 将自动黑名单合并到主配置
python3 << EOF
import json

# 读取自动生成的黑名单
with open('user_data/blacklist_auto_generated.json') as f:
    auto_bl = json.load(f)

# 读取主配置
with open('user_data/config-custom.json') as f:
    config = json.load(f)

# 合并黑名单（保留手动添加的）
manual_bl = set(config.get('pair_blacklist', []))
auto_bl_set = set(auto_bl['pair_blacklist'])
config['pair_blacklist'] = list(manual_bl | auto_bl_set)

# 保存
with open('user_data/config-custom.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ 已更新黑名单: {len(config['pair_blacklist'])}个币种")
EOF

# 4. 重启Bot（如果在运行）
./ft stop --bot && ./ft start --bot -d
```

**自动化（Cron定时任务）：**

```bash
# 每周日凌晨2点运行
0 2 * * 0 cd /home/dministrator/Newproject/freqtrade && ./scripts/detect_toxic_pairs.sh
```

---

### 方案2: 实盘实时监控（进阶）

**原理：** Bot运行时实时监控每个交易对的表现

```python
# 添加到策略文件: user_data/strategies/NostalgiaForInfinityX7.py

class NostalgiaForInfinityX7(IStrategy):

    # 在类初始化时加载
    def __init__(self, config: dict):
        super().__init__(config)
        self.pair_stats = {}  # 存储每个币种的统计数据
        self.toxic_detection_enabled = config.get('toxic_detection_enabled', True)

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                           rate: float, time_in_force: str, current_time,
                           entry_tag, side: str, **kwargs) -> bool:
        """
        在进场前检查币种风险
        """
        if not self.toxic_detection_enabled:
            return True

        # 检查是否为Grind模式
        is_grind = '120' in str(entry_tag)

        if is_grind:
            # 检查该币种是否在风险名单中
            if self.is_pair_toxic(pair):
                logger.warning(f"🚨 {pair} 被识别为高风险币种，拒绝Grind模式进场")
                return False

        return True

    def is_pair_toxic(self, pair: str) -> bool:
        """
        实时检查币种是否为毒瘤
        """
        if pair not in self.pair_stats:
            return False  # 新币种，允许尝试

        stats = self.pair_stats[pair]

        # Level 1: 致命信号
        if stats.get('has_liquidation', False):
            return True

        if stats.get('consecutive_losses', 0) >= 3:  # 连续3次亏损
            return True

        if stats.get('max_drawdown', 0) < -0.20:  # 最大回撤>20%
            return True

        # Level 2: Grind特殊检查
        grind_stats = stats.get('grind', {})
        if grind_stats.get('trades', 0) >= 2:
            if grind_stats.get('win_rate', 100) < 50:  # Grind胜率<50%
                return True
            if grind_stats.get('avg_duration_hours', 0) > 168:  # 平均持仓>7天
                if grind_stats.get('total_profit', 0) < 0:  # 且亏损
                    return True

        return False

    def custom_exit(self, pair: str, trade, current_time, current_rate,
                    current_profit, **kwargs):
        """
        平仓后更新币种统计
        """
        if not self.toxic_detection_enabled:
            return None

        # 更新统计数据
        self.update_pair_stats(pair, trade)

        # 原有的出场逻辑...
        return None

    def update_pair_stats(self, pair: str, trade):
        """
        更新币种统计数据（用于实时监控）
        """
        if pair not in self.pair_stats:
            self.pair_stats[pair] = {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'consecutive_losses': 0,
                'max_drawdown': 0,
                'has_liquidation': False,
                'grind': {
                    'trades': 0,
                    'wins': 0,
                    'total_profit': 0,
                    'durations': []
                }
            }

        stats = self.pair_stats[pair]
        stats['total_trades'] += 1

        # 更新盈亏统计
        if trade.profit_ratio > 0:
            stats['wins'] += 1
            stats['consecutive_losses'] = 0
        else:
            stats['losses'] += 1
            stats['consecutive_losses'] += 1

        # 更新最大回撤
        if trade.profit_ratio < stats['max_drawdown']:
            stats['max_drawdown'] = trade.profit_ratio

        # 检查爆仓
        if 'liquidation' in str(trade.exit_reason):
            stats['has_liquidation'] = True
            logger.error(f"🚨 {pair} 发生爆仓！加入永久黑名单")

        # 更新Grind统计
        if '120' in str(trade.enter_tag):
            grind = stats['grind']
            grind['trades'] += 1
            if trade.profit_ratio > 0:
                grind['wins'] += 1
            grind['total_profit'] += trade.profit_abs
            grind['durations'].append(trade.duration_hours)
```

**配置启用：**

```json
{
  "toxic_detection_enabled": true,
  "toxic_detection_config": {
    "max_consecutive_losses": 3,
    "max_drawdown_threshold": -0.20,
    "grind_win_rate_threshold": 0.50,
    "grind_duration_threshold_hours": 168
  }
}
```

---

### 方案3: 事前市场数据过滤（最先进）

**原理：** 在币种进入交易列表前，用市场数据预判风险

```python
# 创建自定义Pairlist过滤器
# user_data/pairlists/ToxicPairFilter.py

from freqtrade.plugins.pairlist.IPairList import IPairList

class ToxicPairFilter(IPairList):
    """
    基于市场数据的毒瘤币种过滤器

    过滤条件：
    1. 极端波动率（日波动>20%）
    2. 流动性不足（24h交易量<1000万USDT）
    3. 价格操纵迹象（短时间大幅拉升/砸盘）
    """

    def filter_pairlist(self, pairlist, tickers):
        filtered = []

        for pair in pairlist:
            if pair not in tickers:
                continue

            ticker = tickers[pair]

            # 过滤1: 检查波动率
            if self.is_too_volatile(ticker):
                self.log_once(f"过滤 {pair}: 波动率过高", logger.warning)
                continue

            # 过滤2: 检查流动性
            if not self.has_sufficient_liquidity(ticker):
                self.log_once(f"过滤 {pair}: 流动性不足", logger.warning)
                continue

            # 过滤3: 检查价格操纵
            if self.has_manipulation_signs(pair, ticker):
                self.log_once(f"过滤 {pair}: 疑似价格操纵", logger.warning)
                continue

            filtered.append(pair)

        return filtered

    def is_too_volatile(self, ticker):
        """检查波动率是否过高"""
        high = ticker['high']
        low = ticker['low']
        volatility = (high - low) / low

        # 日波动率>20%视为过高
        return volatility > 0.20

    def has_sufficient_liquidity(self, ticker):
        """检查流动性是否充足"""
        volume_usdt = ticker.get('quoteVolume', 0)

        # 24h交易量<1000万USDT视为不足
        return volume_usdt >= 10_000_000

    def has_manipulation_signs(self, pair, ticker):
        """
        检查价格操纵迹象

        特征：
        - 短时间内暴涨暴跌（1小时涨跌>15%）
        - 交易量突增但价格异常
        """
        # 获取1小时K线数据
        ohlcv = self.dp.get_ohlcv(pair, '1h', limit=2)

        if len(ohlcv) < 2:
            return False

        # 计算1小时价格变化
        price_change = (ohlcv[-1]['close'] - ohlcv[-2]['close']) / ohlcv[-2]['close']

        # 1小时涨跌>15%视为异常
        if abs(price_change) > 0.15:
            return True

        return False
```

**配置使用：**

```json
{
  "pairlists": [
    {
      "method": "VolumePairList",
      "number_assets": 80,
      "sort_key": "quoteVolume"
    },
    {
      "method": "ToxicPairFilter"  // ← 添加毒瘤过滤器
    },
    {
      "method": "AgeFilter",
      "min_days_listed": 10
    }
  ]
}
```

---

## 📊 三种方案对比

| 方案 | 实现难度 | 实时性 | 准确度 | 推荐度 |
|------|----------|--------|--------|--------|
| **方案1：定期回测分析** | ⭐ 简单 | 低（周更新） | ⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ |
| **方案2：实盘实时监控** | ⭐⭐ 中等 | 高（实时） | ⭐⭐⭐⭐ 很高 | ⭐⭐⭐⭐ |
| **方案3：事前数据过滤** | ⭐⭐⭐ 复杂 | 很高（进场前） | ⭐⭐ 中等 | ⭐⭐⭐ |

**推荐组合：方案1 + 方案2**
- 方案1作为基础，每周自动更新黑名单
- 方案2作为保险，实盘中实时拒绝高风险交易

---

## 🚀 快速部署指南

### 步骤1：创建分析脚本

```bash
# 创建脚本目录
mkdir -p scripts

# 下载完整脚本（上面的Python代码）
# 保存为: scripts/analyze_toxic_pairs.py
chmod +x scripts/analyze_toxic_pairs.py
```

### 步骤2：首次运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行分析
python3 scripts/analyze_toxic_pairs.py

# 查看结果
cat user_data/blacklist_auto_generated.json
```

### 步骤3：配置自动化

```bash
# 添加到crontab
crontab -e

# 添加这行：每周日凌晨2点运行
0 2 * * 0 cd /home/dministrator/Newproject/freqtrade && source .venv/bin/activate && python3 scripts/analyze_toxic_pairs.py
```

### 步骤4：手动合并黑名单（可选）

```bash
# 将自动黑名单合并到主配置
python3 << EOF
import json

with open('user_data/blacklist_auto_generated.json') as f:
    auto = json.load(f)

with open('user_data/config-custom.json') as f:
    config = json.load(f)

config['pair_blacklist'] = list(set(config.get('pair_blacklist', [])) | set(auto['pair_blacklist']))

with open('user_data/config-custom.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 黑名单已更新")
EOF
```

---

## 💡 最佳实践

### 1. 分级管理黑名单

```json
{
  "pair_blacklist": [
    "INJ/USDT:USDT",   // Level 1: 永久黑名单（爆仓）
    "CRV/USDT:USDT"    // Level 1: 永久黑名单（爆仓）
  ],

  "nfi_parameters": {
    "blacklist_120_pairs": [  // Level 2: 仅禁用Grind
      "XRP/USDT:USDT",        // 胜率低
      "ALGO/USDT:USDT"        // Grind表现差
    ]
  }
}
```

### 2. 定期审查（每月）

```bash
# 检查黑名单是否仍然有效
python3 << EOF
import json

with open('user_data/blacklist_auto_generated.json') as f:
    data = json.load(f)

print("当前黑名单:")
for item in data['details']['toxic_pairs']:
    print(f"  {item['pair']}: {item['reason']}")

print("\n警告名单:")
for item in data['details']['warning_pairs']:
    print(f"  {item['pair']}: {', '.join(item['signals'])}")
EOF
```

### 3. 配置告警

```python
# 在策略中添加Telegram告警
def update_pair_stats(self, pair: str, trade):
    # ... 更新逻辑 ...

    if self.is_pair_toxic(pair):
        self.dp.send_msg(f"🚨 警告：{pair} 被识别为高风险币种！\n"
                        f"建议：考虑加入黑名单")
```

---

## 📈 效果评估

定期运行回测对比：

```bash
# 对比启用vs不启用毒瘤检测
freqtrade backtesting --config config-with-detection.json
freqtrade backtesting --config config-without-detection.json

# 比较：
# - 总收益
# - 最大回撤
# - 长期持仓交易数量
```

预期效果：
- 总收益：提升30-80%
- 最大回撤：降低40-60%
- 长期深套：减少至0

---

## 🔧 故障排除

**Q: 脚本运行报错找不到回测文件？**
```bash
# 手动指定最新回测文件
python3 scripts/analyze_toxic_pairs.py --input user_data/backtest_results/backtest-result-2025-11-06_20-52-16.json
```

**Q: 如何临时禁用某个币种的Grind？**
```json
{
  "nfi_parameters": {
    "blacklist_120_pairs": ["PAIR/USDT:USDT"]
  }
}
```

**Q: 如何查看某个币种的详细统计？**
```python
python3 << EOF
from scripts.analyze_toxic_pairs import get_pair_stats

stats = get_pair_stats("INJ/USDT:USDT")
print(json.dumps(stats, indent=2))
EOF
```
