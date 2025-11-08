# 黑名单更新记录

**更新日期**: 2025-11-08
**更新原因**: 基于6个月回测分析(2025-05-01至2025-11-07)识别的负收益币种
**回测策略**: NostalgiaForInfinityX7
**数据来源**: docs/TOXIC_PAIRS_ANALYSIS_2025-11-08.md

## 本次更新内容

### 新增黑名单币种 (5个)

根据回测分析,以下币种在6个月测试期间产生净亏损,已添加至`configs/blacklist-binance.json`:

| 币种 | 总收益% | 总收益USDT | 交易数 | 胜率% | 平均持仓 | 添加原因 |
|------|---------|------------|--------|-------|----------|----------|
| **HOOK/USDT:USDT** | -6.02% | -60.177 | 3 | 33.3% | 0:37:00 | 最差表现,胜率极低 |
| **MINA/USDT:USDT** | -5.88% | -58.761 | 2 | 50.0% | 5:00:00 | 高额亏损 |
| **KAIA/USDT:USDT** | -3.10% | -30.983 | 2 | 50.0% | 1:42:00 | 净亏损 |
| **BAND/USDT:USDT** | -2.88% | -28.835 | 2 | 50.0% | 0:18:00 | 净亏损 |
| **HIGH/USDT:USDT** | -2.00% | -19.979 | 2 | 50.0% | 0:15:00 | 净亏损 |

**注**: GMX/USDT:USDT 虽然回测中亏损-2.77%,但已经在黑名单中,无需重复添加。

### 总计
- **新增币种数**: 5个
- **预期避免总亏损**: 约198.735 USDT
- **黑名单总币种数**: 约280+个

## 更新位置

**文件**: `configs/blacklist-binance.json`
**更新行**: 第16行 - 问题代币和低流动性代币类别
**更新方式**: 在正则表达式模式中追加新币种

### 更新前 (片段)
```
...PERP|AI16Z|XPIN|CUDIS|H|MAGIC|GMX|NEAR|SOL|PENDLE)/.*
```

### 更新后 (片段)
```
...PERP|AI16Z|XPIN|CUDIS|H|MAGIC|GMX|NEAR|SOL|PENDLE|HOOK|MINA|KAIA|BAND|HIGH)/.*
```

## 验证建议

### 1. 配置验证
```bash
# 验证JSON格式正确性
python3 -m json.tool configs/blacklist-binance.json > /dev/null && echo "✅ JSON格式正确"

# 测试pairlist生成(需要设置代理)
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
freqtrade test-pairlist --config user_data/config-custom.json --config user_data/config-private.json --quote USDT
```

### 2. 确认黑名单生效
运行test-pairlist后,确认以下币种**不**出现在结果中:
- HOOK/USDT:USDT
- MINA/USDT:USDT
- KAIA/USDT:USDT
- BAND/USDT:USDT
- HIGH/USDT:USDT

### 3. 实盘前检查
- [ ] 确认黑名单已生效
- [ ] 检查当前持仓是否包含已加入黑名单的币种
- [ ] 如有持仓,手动平仓或等待策略自动退出
- [ ] 重启机器人使配置生效

## 未处理的零交易币种

以下16个币种在回测中完全无法触发交易信号,但**未加入黑名单**,因为它们可能在其他市场环境下有效:

- 1INCH, ACT, AI, BTC, CELO, EGLD, ENA, ENJ
- FLOW, FLUID, GMT, KAVA, MANA, PENDLE, USDC, ZK

**建议**:
- 保留在候选池中观察
- 如果后续12个月回测仍无信号,再考虑加入黑名单
- BTC无信号值得特别关注(可能是策略参数问题)

## 影响评估

### 正面影响
1. **减少亏损**: 预计避免约200 USDT亏损
2. **提高效率**: 减少无效交易和监控成本
3. **风险控制**: 避免策略不适配币种的潜在风险

### 潜在风险
1. **机会成本**: 这些币种在未来可能表现改善
2. **样本时间**: 仅6个月数据,可能不够全面
3. **市场环境变化**: 熊市/牛市表现可能不同

### 缓解措施
- 每季度重新评估黑名单
- 扩展回测至12个月验证
- 监控市场整体环境变化

## 相关文档

- **详细分析报告**: `docs/TOXIC_PAIRS_ANALYSIS_2025-11-08.md`
- **回测结果**: `user_data/backtest_results/backtest-result-2025-11-08_04-57-52.zip`
- **黑名单配置**: `configs/blacklist-binance.json`
- **回测日志**: `backtest_output.log`

## 下次审查计划

**建议审查时间**: 2026-02-08 (3个月后)

**审查内容**:
1. 重新回测已加入黑名单的5个币种
2. 评估零交易的16个币种状态
3. 分析整体策略表现变化
4. 根据市场环境调整黑名单策略

---

**更新执行**: Claude Code Backtest Analyzer
**批准状态**: 待用户确认
**生效时间**: 机器人重启后
