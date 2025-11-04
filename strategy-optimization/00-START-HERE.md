# 策略优化项目 - 快速导航

**创建日期**: 2025-11-04
**项目状态**: ✅ 分析完成，方案就绪

---

## 🚀 从这里开始

### 第一次使用？

1. **返回项目根目录**
   ```bash
   cd ..
   ```

2. **阅读总览文档**
   ```bash
   cat README_OPTIMIZATION.md
   ```

3. **运行快速启动脚本**
   ```bash
   ./quick_start_optimization.sh
   ```

---

## 📁 文件夹结构

```
strategy-optimization/
├── 00-START-HERE.md           ← 你在这里
│
├── docs/                      ← 📚 所有文档
│   ├── OPTIMIZATION_SUMMARY.md            (6.6KB) - 快速总览
│   ├── BACKTEST_SIGNAL_ANALYSIS_REPORT.md (6.2KB) - 深度分析
│   ├── STRATEGY_OPTIMIZATION_PLAN.md      (16KB)  - 详细方案
│   └── OPTIMIZATION_CHECKLIST.md          (8.2KB) - 执行清单
│
├── analysis-data/             ← 📊 原始分析数据
│   ├── analysis_group_012.txt    (114KB) - 基础信号分析
│   ├── analysis_group_3.txt      (53KB)  - 交易对+信号分析
│   ├── analysis_group_5.txt      (83KB)  - 出场标签分析
│   ├── analysis_basic.txt        (3.4KB) - 基础分析
│   ├── analysis_basic_full.txt   (1.2KB) - 完整配置分析
│   └── analysis_rejected.txt     (4.1KB) - 拒绝信号分析
│
└── logs/                      ← 📝 日志文件
    └── backtest_with_signals.log - 回测运行日志
```

---

## 📖 推荐阅读顺序

### 🔰 新手（第一次优化）

1. **快速了解** (5分钟)
   ```bash
   cd docs
   cat OPTIMIZATION_SUMMARY.md
   ```

2. **理解问题** (15分钟)
   ```bash
   cat BACKTEST_SIGNAL_ANALYSIS_REPORT.md
   ```

3. **学习方案** (30分钟)
   ```bash
   cat STRATEGY_OPTIMIZATION_PLAN.md
   ```

4. **开始执行** (按计划)
   ```bash
   cat OPTIMIZATION_CHECKLIST.md
   ```

---

### 💼 快速查阅

```bash
# 查看所有文档
ls -lh docs/

# 查看所有分析数据
ls -lh analysis-data/

# 查看关键发现（分析报告摘要）
head -100 docs/BACKTEST_SIGNAL_ANALYSIS_REPORT.md

# 查看第一周任务清单
grep -A 50 "第1周" docs/OPTIMIZATION_CHECKLIST.md
```

---

## 🎯 关键问题诊断（快速参考）

### 🚨 当前严重问题

| 问题 | 数据 | 文档位置 |
|------|------|---------|
| **爆仓** | 50次，-37,909 USDT | `docs/BACKTEST_SIGNAL_ANALYSIS_REPORT.md` |
| **最大回撤** | 信号 62 141 144, -9,420 USDT | `analysis-data/analysis_group_3.txt:32` |
| **杠杆过高** | 10倍 | `docs/STRATEGY_OPTIMIZATION_PLAN.md` |

### ✅ 发现的优势

| 优势 | 数据 | 文档位置 |
|------|------|---------|
| **信号 145** | 87笔，90.8%胜率，+25,561 USDT | `analysis-data/analysis_group_012.txt` |
| **信号 142** | 83笔，95.2%胜率，+22,862 USDT | `analysis-data/analysis_group_012.txt` |
| **AVAX+142 144** | +6,197 USDT (+174%) | `analysis-data/analysis_group_3.txt:297` |

---

## 🔧 快速命令

### 查看特定分析

```bash
# 查看入场信号分析
cat analysis-data/analysis_group_012.txt

# 查看交易对表现
cat analysis-data/analysis_group_3.txt

# 查看出场分析
cat analysis-data/analysis_group_5.txt

# 查看回测日志
cat logs/backtest_with_signals.log
```

### 搜索关键信息

```bash
# 搜索信号 145 的所有出现
grep -r "145" analysis-data/

# 搜索爆仓相关
grep -i "liquidation" analysis-data/

# 搜索最大回撤
grep -i "62 141 144" analysis-data/
```

---

## 📊 回测数据位置

完整的回测数据（含信号数据）存储在：

```
../user_data/backtest_results/backtest-result-2025-11-04_14-23-15.zip (4.9MB)
```

包含：
- 交易记录
- 信号数据（_signals.pkl）
- 出场数据（_exited.pkl）
- 拒绝信号（_rejected.pkl）
- 配置文件

---

## 📝 维护建议

### 每次优化后

1. **记录结果**
   - 在 `logs/` 中添加新的回测日志
   - 更新文档中的数据

2. **版本控制**
   ```bash
   git add strategy-optimization/
   git commit -m "update: optimization results for phase X"
   ```

3. **对比分析**
   - 保留每个阶段的分析数据
   - 创建对比报告

---

## ⚠️ 重要提醒

- 📍 **主入口在根目录**: `../README_OPTIMIZATION.md`
- 🚀 **启动脚本在根目录**: `../quick_start_optimization.sh`
- 💾 **回测数据在**: `../user_data/backtest_results/`
- 📚 **详细文档在**: `docs/`

---

## 🔗 相关文件链接

### 根目录文件
- `../README_OPTIMIZATION.md` - 主索引文档
- `../quick_start_optimization.sh` - 一键启动脚本

### 配置文件（待创建）
- `../user_data/config-optimized-v2-safe.json` - 优化后配置

### 策略文件（待创建）
- `../user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py`

---

## 📞 需要帮助？

1. **查看总览**: `cat ../README_OPTIMIZATION.md`
2. **查看方案**: `cat docs/STRATEGY_OPTIMIZATION_PLAN.md`
3. **查看清单**: `cat docs/OPTIMIZATION_CHECKLIST.md`

---

**准备好开始优化了吗？**

```bash
# 返回根目录
cd ..

# 运行快速启动
./quick_start_optimization.sh
```

---

*导航文件自动生成*
*最后更新: 2025-11-04*
