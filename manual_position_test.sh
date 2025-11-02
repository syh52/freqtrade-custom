#!/bin/bash
# 手动仓位优化测试 - 简化版
# 只测试最关键的几个参数组合

cd /home/dministrator/Newproject/freqtrade
source .venv/bin/activate

# 创建结果目录
mkdir -p position_optimization_results

echo "================================"
echo "手动仓位优化测试"
echo "配置: ETH_AVAX (最推荐)"
echo "================================"
echo

# 测试1: 5x杠杆
echo "=== 测试1: 5x杠杆 (5仓位) ==="
python3 <<'PYTHON1'
import json
with open('user_data/config.json', 'r') as f:
    config = json.load(f)
config['exchange']['pair_whitelist'] = [
    "XRP/USDT:USDT", "BNB/USDT:USDT", "SOL/USDT:USDT",
    "DOGE/USDT:USDT", "ADA/USDT:USDT", "LINK/USDT:USDT",
    "ETH/USDT:USDT", "AVAX/USDT:USDT"
]
config['max_open_trades'] = 5
# 注意：freqtrade的leverage在exchange层面设置，不是在策略中
# 这里只能测试不同的max_open_trades
with open('user_data/config.json', 'w') as f:
    json.dump(config, f, indent=4)
print("✓ 配置已更新: max_open_trades=5")
PYTHON1

freqtrade backtesting -s NostalgiaForInfinityX7 \
  --timerange 20240101-20241031 \
  -c user_data/config.json \
  > position_optimization_results/ETH_AVAX_5trades.log 2>&1

echo "✓ 测试1完成"
echo

# 测试2: 3仓位
echo "=== 测试2: 3仓位 ==="
python3 <<'PYTHON2'
import json
with open('user_data/config.json', 'r') as f:
    config = json.load(f)
config['max_open_trades'] = 3
with open('user_data/config.json', 'w') as f:
    json.dump(config, f, indent=4)
print("✓ 配置已更新: max_open_trades=3")
PYTHON2

freqtrade backtesting -s NostalgiaForInfinityX7 \
  --timerange 20240101-20241031 \
  -c user_data/config.json \
  > position_optimization_results/ETH_AVAX_3trades.log 2>&1

echo "✓ 测试2完成"
echo

# 测试3: 7仓位
echo "=== 测试3: 7仓位 ==="
python3 <<'PYTHON3'
import json
with open('user_data/config.json', 'r') as f:
    config = json.load(f)
config['max_open_trades'] = 7
with open('user_data/config.json', 'w') as f:
    json.dump(config, f, indent=4)
print("✓ 配置已更新: max_open_trades=7")
PYTHON3

freqtrade backtesting -s NostalgiaForInfinityX7 \
  --timerange 20240101-20241031 \
  -c user_data/config.json \
  > position_optimization_results/ETH_AVAX_7trades.log 2>&1

echo "✓ 测试3完成"
echo

# 恢复默认配置
python3 <<'PYTHON4'
import json
with open('user_data/config.json', 'r') as f:
    config = json.load(f)
config['max_open_trades'] = 5
with open('user_data/config.json', 'w') as f:
    json.dump(config, f, indent=4)
print("✓ 恢复默认配置: max_open_trades=5")
PYTHON4

echo
echo "================================"
echo "所有测试完成！"
echo "================================"
echo
echo "查看结果:"
echo "  cd position_optimization_results"
echo "  ls -lh"
echo

# 提取关键指标
echo "=== 快速对比 ==="
for log in position_optimization_results/ETH_AVAX_*.log; do
    name=$(basename "$log" .log)
    profit=$(grep "Absolute profit" "$log" | awk '{print $4}')
    liq=$(grep -c "liquidation" "$log")
    trades=$(grep "Total/Daily Avg Trades" "$log" | awk '{print $4}')
    echo "$name: 利润=$profit USDT, 交易=$trades, 爆仓=$liq"
done
