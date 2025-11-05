# 🚀 动态杠杆优化 - 快速启动指南

> 3分钟开始测试动态杠杆策略

---

## ⚡ 超快速启动（1条命令）

```bash
./test_dynamic_leverage.sh
```

这将自动对比原版 vs 动态杠杆策略，无需任何配置！

---

## 📊 这个优化做了什么？

### 一句话总结

**高风险信号用 3x 杠杆，稳健信号保持 10x 杠杆**

### 具体变化

| 信号 | 原杠杆 | 新杠杆 | 原因 |
|------|--------|--------|------|
| #62 | 10x | **3x** | 26次爆仓 ❌ |
| #141 | 10x | **3x** | 13次爆仓 ❌ |
| #144 | 10x | **3x** | 11次爆仓 ❌ |
| #41-46 | 10x | **3x** | Pump模式高风险 |
| #142 | 10x | **10x** | 95.2%胜率 ⭐ |
| #145 | 10x | **10x** | 90.8%胜率 ⭐ |
| 其他 | 10x | **10x** | 保持不变 |

---

## 🎯 预期效果

```
✅ 爆仓次数: 50 → <10 (-80%)
✅ 最大回撤: -176% → ~-40% (-77%)
✅ 风险降低: 爆仓点从 -10% → -33% (3.3倍安全边际)
✅ 保持盈利: #142, #145 等信号仍用 10x
```

---

## 🧪 开始测试

### 步骤 1: 运行回测（自动）

```bash
# 默认测试最近3个月
./test_dynamic_leverage.sh

# 或指定时间范围
./test_dynamic_leverage.sh 20240101-20241031
```

### 步骤 2: 查看结果

脚本会自动显示对比结果，重点关注：

1. **Liquidations**（爆仓次数）- 应该大幅减少
2. **Max Drawdown**（最大回撤）- 应该从 -176% 降至 ~-40%
3. **Total Profit**（总利润）- 可能略有下降，但更安全
4. **Sharpe Ratio**（风险调整收益）- 应该提升

### 步骤 3: 查看详细日志

```bash
# 查看原版策略日志
cat backtest_results/dynamic_leverage_comparison/backtest_original.log

# 查看动态杠杆策略日志
cat backtest_results/dynamic_leverage_comparison/backtest_dynamic.log
```

---

## 📖 查看文档

```bash
# 完整说明（推荐阅读）
cat DYNAMIC_LEVERAGE_README.md

# DCA 说明
cat DCA_EXPLAINED.md

# 策略概览
cat STRATEGY_OVERVIEW_COMPLETE.md
```

---

## 🔧 自定义配置（可选）

### 修改高风险杠杆倍数

编辑 `user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py` 第 180 行：

```python
# 当前: 3x
futures_mode_leverage_high_risk = 3.0

# 改为 2x（更保守）
futures_mode_leverage_high_risk = 2.0

# 改为 5x（略保守）
futures_mode_leverage_high_risk = 5.0
```

### 修改高风险信号列表

编辑第 183-189 行：

```python
high_risk_signals = [
    "62", "141", "144",    # 最危险的3个
    # 可以移除或添加其他信号
]
```

---

## 💡 理解代码修改

### 查看修改的地方

```bash
# 使用交互式查看器
./view_strategy.sh
选择: 44
输入: leverage

# 或直接查看
sed -n '11559,11585p' user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py
```

### 核心修改

```python
def leverage(self, ...):
    # 新增：检查是否为高风险信号
    for tag in enter_tags:
        signal_num = tag.split("_")[0]
        if signal_num in self.high_risk_signals:
            return self.futures_mode_leverage_high_risk  # 返回 3x

    # 原逻辑：其他信号保持 10x
    ...
```

---

## ✅ 完整工作流程

### 测试阶段

```bash
# 1. 回测对比
./test_dynamic_leverage.sh

# 2. 分析结果（重点看爆仓和回撤）
#    如果效果好 → 进入下一步
#    如果不理想 → 调整杠杆倍数或信号列表
```

### 验证阶段（回测效果好才进行）

```bash
# 3. 模拟交易（Dry-run）
source .venv/bin/activate

freqtrade trade \
  --strategy NostalgiaForInfinityX7_DynamicLeverage \
  --config user_data/config.json \
  --dry-run
```

### 实盘阶段（模拟交易稳定才进行）

```bash
# 4. 小资金实盘（谨慎！）
#    - 从可承受损失的小金额开始
#    - 持续监控1-2周
#    - 确认稳定后再增加资金
```

---

## 🎁 创建的文件列表

```
user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py  (优化策略)
test_dynamic_leverage.sh                                         (测试脚本)
DYNAMIC_LEVERAGE_README.md                                       (完整文档)
QUICK_START_DYNAMIC_LEVERAGE.md                                 (本文件)
```

---

## ⚠️ 重要提示

1. **这不是零风险**
   - 只是降低风险，10x 对稳健信号仍然较高
   - 建议结合其他优化（调整止损、减少DCA）

2. **回测不代表未来**
   - 市场会变化
   - 需要持续监控和调整

3. **从小开始**
   - 即使回测效果好，也要从小资金开始
   - 逐步增加，不要一次投入大量资金

---

## 🆘 遇到问题？

### 策略文件找不到

```bash
# 检查文件是否存在
ls user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py

# 如果不存在，重新创建
git checkout user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py
```

### 回测失败

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 确保数据已下载
freqtrade download-data --days 120

# 手动运行回测看错误
freqtrade backtesting --strategy NostalgiaForInfinityX7_DynamicLeverage
```

### 查看更多帮助

```bash
# 查看策略列表
freqtrade list-strategies

# 查看回测帮助
freqtrade backtesting --help
```

---

## 📞 获取更多帮助

- **DCA 不理解？** → `cat DCA_EXPLAINED.md`
- **策略太复杂？** → `./view_strategy.sh` 交互式浏览
- **想了解信号？** → `cat STRATEGY_OVERVIEW_COMPLETE.md`
- **要优化计划？** → `cat strategy-optimization/docs/STRATEGY_OPTIMIZATION_PLAN.md`

---

## 🚀 现在就开始

```bash
./test_dynamic_leverage.sh
```

简单一条命令，让我们看看动态杠杆能带来多大改善！

---

**创建时间**: 2025-11-05
**版本**: 1.0
**预计测试时间**: 5-10分钟（取决于数据量）
