# NostalgiaForInfinityX7 策略概览

> 自动生成于策略分析工具

## 📑 快速导航

| 章节 | 描述 |
|------|------|
| [核心配置](#核心配置) | 止损、时间框架、ROI等关键参数 |
| [方法统计](#方法统计) | 策略包含的所有方法分类统计 |
| [入场信号](#入场信号) | 所有入场信号编号和位置 |
| [出场机制](#出场机制) | 退出条件和保护措施 |
| [关键方法](#关键方法) | 核心交易逻辑方法详情 |

## 🔧 核心配置

```python
INTERFACE_VERSION = 3
```

## 📊 方法统计

- **总方法数**: 113
- **入场条件**: 0 个
- **出场条件**: 34 个

## 🎯 入场信号

| 信号编号 | 方法名 | 代码行 |
|---------|--------|-------|

## 🔑 关键方法

| 方法名 | 描述 | 代码行 |
|--------|------|--------|
| `populate_indicators` | 添加技术指标到数据框 | 3763 |
| `populate_entry_trend` | 标记入场信号 | 11797 |
| `populate_exit_trend` | 标记出场信号 | 11767 |
| `custom_stake_amount` | 自定义每笔交易的投入金额 | 2257 |
| `adjust_trade_position` | DCA/加仓逻辑 | 2401 |
| `custom_exit` | 自定义退出条件 | 1700 |
| `confirm_trade_entry` | 入场前的最终确认 | 11385 |
| `confirm_trade_exit` | 出场前的最终确认 | 11501 |

---

### 💡 使用建议

1. **查看特定方法**: `sed -n '<行号>,+100p' user_data/strategies/NostalgiaForInfinityX7.py`
2. **搜索关键字**: `grep -n '关键字' user_data/strategies/NostalgiaForInfinityX7.py`
3. **使用代码编辑器**: VS Code, PyCharm 等可以提供更好的导航
