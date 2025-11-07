# 策略更新日志

## 2025-11-07: NostalgiaForInfinityX7 策略更新

### 更新摘要
从 v17.1.94 升级到原作者最新版本 v17.1.113，并配置为14倍杠杆期货交易。

### 变更详情

#### 1. 策略文件更新
- **原版本**: v17.1.94 (已备份为 `NostalgiaForInfinityX7_v17.1.94_backup.py`)
- **新版本**: v17.1.113 (原作者最新版)
- **来源**: https://github.com/iterativv/NostalgiaForInfinity.git
- **文件位置**: `user_data/strategies/NostalgiaForInfinityX7.py`

#### 2. 杠杆参数修改
策略文件中的杠杆参数从 3.0 修改为 14.0：
```python
futures_mode_leverage = 14.0  # 原值: 3.0
futures_mode_leverage_rebuy_mode = 14.0  # 原值: 3.0
futures_mode_leverage_grind_mode = 14.0  # 原值: 3.0
```

#### 3. 配置文件更新 (`user_data/config-custom.json`)
```json
{
  "max_open_trades": 11,  // 原值: 10
  "futures_mode_leverage": 14.0,
  "futures_mode_leverage_rebuy_mode": 14.0,
  "futures_mode_leverage_grind_mode": 14.0,
  "nfi_parameters": {
    "futures_max_open_trades_long": 10,  // 原值: 9
    "futures_max_open_trades_short": 1   // 保持不变
  }
}
```

### 配置总结
- **交易模式**: 期货交易 (futures, isolated margin)
- **杠杆倍数**: 14倍
- **最大开仓**: 11个 (10多单 + 1空单)
- **策略版本**: NostalgiaForInfinityX7 v17.1.113

### 备份文件
- `user_data/strategies/NostalgiaForInfinityX7_v17.1.94_backup.py`

### 回滚方法
如需回滚到旧版本：
```bash
cp user_data/strategies/NostalgiaForInfinityX7_v17.1.94_backup.py user_data/strategies/NostalgiaForInfinityX7.py
```

### 验证步骤
更新后建议执行以下验证：
1. 检查策略版本: `freqtrade list-strategies`
2. 测试配置: `freqtrade test-pairlist --config user_data/config-custom.json`
3. 回测验证: `freqtrade backtesting --strategy NostalgiaForInfinityX7 --timerange <your_range>`

### 注意事项
- ⚠️ 14倍杠杆风险较高，请谨慎使用
- ⚠️ 建议先在测试环境或小资金测试
- ⚠️ 原作者推荐6-12个开仓，40-80对交易对
- ⚠️ 必须使用5分钟时间框架（不可修改）
