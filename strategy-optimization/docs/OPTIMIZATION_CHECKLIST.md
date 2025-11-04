# 策略优化执行检查清单

**开始日期**: ___________
**目标完成日期**: ___________

---

## ✅ 第1周：紧急风控部署（Day 1-7）

### Day 1-2: 杠杆调整

- [ ] **备份当前版本**
  ```bash
  git add .
  git commit -m "backup: before optimization - baseline"
  git tag v1.0-baseline
  ```

- [ ] **创建优化分支**
  ```bash
  git checkout -b feature/risk-optimization-phase1
  ```

- [ ] **创建新配置文件**
  ```bash
  cp user_data/config-backtest-nfx7-nogrind-55pairs.json \
     user_data/config-optimized-v2-safe.json
  ```

- [ ] **修改杠杆参数**（在 `config-optimized-v2-safe.json`）
  - [ ] 将 `leverage` 从 10 改为 6
  - [ ] 设置 `liquidation_buffer` 为 0.10
  - [ ] 设置 `max_open_trades` 为 3

- [ ] **运行对比回测**
  ```bash
  freqtrade backtesting \
    --config user_data/config-optimized-v2-safe.json \
    --strategy NostalgiaForInfinityX7_NoGrind \
    --timerange 20241103-20251102 \
    --breakdown day
  ```

- [ ] **记录结果**
  - 爆仓次数: _____ (目标: < 5次)
  - 最大回撤: _____ (目标: < -30%)
  - 总收益: _____ (目标: 正值或减少70%亏损)

---

### Day 3-4: 止损优化

- [ ] **复制策略文件**
  ```bash
  cp user_data/strategies/NostalgiaForInfinityX7_NoGrind.py \
     user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py
  ```

- [ ] **修改策略类名**
  ```python
  class NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss(IStrategy):
  ```

- [ ] **修改止损参数**
  ```python
  stoploss = -0.15  # 从 -0.99 改为 -0.15
  ```

- [ ] **添加追踪止损**
  ```python
  trailing_stop = True
  trailing_stop_positive = 0.01
  trailing_stop_positive_offset = 0.03
  trailing_only_offset_is_reached = True
  ```

- [ ] **（可选）添加动态止损函数**
  - 参考优化方案中的 `custom_stoploss()` 代码

- [ ] **运行回测验证**
  ```bash
  freqtrade backtesting \
    --config user_data/config-optimized-v2-safe.json \
    --strategy NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss \
    --timerange 20241103-20251102
  ```

- [ ] **记录结果**
  - 止损触发次数: _____
  - 平均止损损失: _____
  - 总收益变化: _____

---

### Day 5-6: 禁用危险信号

- [ ] **在策略中添加信号黑名单**
  ```python
  # 在 populate_entry_trend() 函数开头添加
  def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
      # 信号黑名单
      blacklist_signals = [
          '62 141 144',  # 最大回撤来源
      ]

      # ... 其余代码
  ```

- [ ] **添加信号过滤逻辑**
  ```python
  # 在函数末尾，return 之前添加
  for signal in blacklist_signals:
      if 'enter_tag' in dataframe.columns:
          mask = dataframe['enter_tag'].astype(str).str.contains(signal, na=False)
          dataframe.loc[mask, 'enter_long'] = 0
  ```

- [ ] **运行回测验证**

- [ ] **记录结果**
  - 被过滤的信号数: _____
  - 总交易次数变化: _____
  - 收益变化: _____

---

### Day 7: 第一周验证

- [ ] **生成完整回测报告**
  ```bash
  freqtrade backtesting \
    --config user_data/config-optimized-v2-safe.json \
    --strategy NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss \
    --timerange 20241103-20251102 \
    --export trades,signals \
    --breakdown day week month
  ```

- [ ] **对比基准性能**
  - [ ] 创建对比表格
  - [ ] 检查是否达成目标

- [ ] **决策点**
  - [ ] ✅ 如果达标 → 继续第2周
  - [ ] ❌ 如果未达标 → 调整参数重新测试

- [ ] **提交第一周成果**
  ```bash
  git add .
  git commit -m "feat: phase1 risk control optimization completed"
  git tag v2.0-phase1-complete
  ```

**第一周成功标准**:
- [ ] 爆仓交易 < 5笔 ✓/✗
- [ ] 最大单笔回撤 < -30% ✓/✗
- [ ] 整体收益为正或亏损减少70%以上 ✓/✗

---

## ✅ 第2周：信号质量优化（Day 8-14）

### Day 8-9: 仓位管理

- [ ] **添加 `custom_stake_amount()` 函数**
  - 参考优化方案中的完整代码

- [ ] **修改配置文件**
  ```json
  {
    "stake_amount": "unlimited",
    "tradable_balance_ratio": 0.33,
    "max_open_trades": 3
  }
  ```

- [ ] **回测验证**

- [ ] **记录结果**
  - 高质量信号收益: _____
  - 低质量信号收益: _____
  - 整体收益变化: _____

---

### Day 10-11: 交易对筛选

- [ ] **更新交易对白名单**
  - 参考优化方案中的分层列表

- [ ] **添加交易对黑名单**
  ```json
  "pair_blacklist": [
    "APE/USDT:USDT",
    "CRV/USDT:USDT",
    "ARB/USDT:USDT"
  ]
  ```

- [ ] **回测验证**

- [ ] **记录结果**
  - 白名单交易对表现: _____
  - 黑名单交易对排除效果: _____

---

### Day 12-13: 入场确认优化

- [ ] **添加 `confirm_trade_entry()` 函数**

- [ ] **实施双重确认机制**

- [ ] **回测验证**

- [ ] **记录结果**
  - 被拒绝的交易数: _____
  - 拒绝交易的平均预期收益: _____

---

### Day 14: 第二周验证

- [ ] **完整回测**

- [ ] **对比上周结果**

- [ ] **决策点**
  - [ ] ✅ 达标 → 继续第3周
  - [ ] ❌ 未达标 → 调整

- [ ] **提交成果**
  ```bash
  git commit -m "feat: phase2 signal quality optimization completed"
  git tag v2.1-phase2-complete
  ```

**第二周成功标准**:
- [ ] 胜率 > 60% ✓/✗
- [ ] 盈亏比 > 1.5 ✓/✗
- [ ] 总收益率 > 10% ✓/✗

---

## ✅ 第3周：出场策略优化（Day 15-21）

### Day 15-17: 自定义出场

- [ ] **添加 `custom_exit()` 函数**

- [ ] **实施盈利保护机制**

- [ ] **添加时间管理**

- [ ] **回测验证**

---

### Day 18-19: 综合优化

- [ ] **微调所有参数**

- [ ] **多时间段回测**

- [ ] **压力测试**

---

### Day 20-21: 第三周验证

- [ ] **完整回测**

- [ ] **生成性能报告**

- [ ] **决策点**

- [ ] **提交成果**
  ```bash
  git commit -m "feat: phase3 exit strategy optimization completed"
  git tag v2.2-phase3-complete
  ```

**第三周成功标准**:
- [ ] 夏普比率 > 1.5 ✓/✗
- [ ] 最大回撤 < 20% ✓/✗
- [ ] 盈利因子 > 2.0 ✓/✗

---

## ✅ 第4周：稳定性验证（Day 22-28）

### Day 22-23: 多市场回测

- [ ] **牛市回测** (时间段: _______)
- [ ] **熊市回测** (时间段: _______)
- [ ] **震荡市回测** (时间段: _______)

- [ ] **记录各市场表现**
  - 牛市收益: _____
  - 熊市收益: _____
  - 震荡市收益: _____

---

### Day 24-25: 参数敏感性测试

- [ ] **杠杆敏感性** (测试 4x, 6x, 8x)
- [ ] **止损敏感性** (测试 -10%, -15%, -20%)
- [ ] **仓位比例敏感性**

- [ ] **记录结果**
  - 最佳参数组合: _____
  - 参数稳定性评分: _____

---

### Day 26-27: 最新数据验证

- [ ] **使用最新30天数据回测**

- [ ] **检查过拟合迹象**

- [ ] **实时模拟（如果可能）**

---

### Day 28: 最终验证与部署准备

- [ ] **编写策略文档**
  - [ ] 参数说明
  - [ ] 风险提示
  - [ ] 使用指南

- [ ] **准备监控脚本**

- [ ] **最终决策**
  - [ ] ✅ 准备好实盘测试
  - [ ] ❌ 需要进一步优化

- [ ] **合并到主分支**
  ```bash
  git checkout develop
  git merge feature/risk-optimization-phase1
  git tag v2.0-production-ready
  ```

**第四周成功标准**:
- [ ] 多个市场环境均盈利 ✓/✗
- [ ] 参数变化不显著影响表现 ✓/✗
- [ ] 最新数据回测稳定 ✓/✗

---

## 📊 最终验收标准

### 必须达成（不可妥协）

- [ ] 爆仓次数 < 5笔
- [ ] 最大回撤 < -30%
- [ ] 总收益率 > 10%
- [ ] 胜率 > 55%

### 期望达成（尽力而为）

- [ ] 夏普比率 > 1.5
- [ ] 盈利因子 > 2.0
- [ ] 胜率 > 60%
- [ ] 盈亏比 > 2.0

### 额外加分项

- [ ] 最大回撤 < -20%
- [ ] 夏普比率 > 2.0
- [ ] 月度稳定盈利

---

## 🚨 中止条件

如果出现以下情况，立即停止并重新评估：

- [ ] 优化后爆仓次数反而增加
- [ ] 胜率显著下降（<45%）
- [ ] 出现新的极端亏损
- [ ] 参数极度敏感，微调即崩溃

---

## 📝 每日记录模板

**日期**: _____
**今日任务**: _____
**完成情况**: _____
**关键发现**: _____
**问题记录**: _____
**明日计划**: _____

---

**打印此清单，逐项勾选，确保不遗漏任何重要步骤！**

*检查清单由 Claude Code 生成*
*创建时间: 2025-11-04*
