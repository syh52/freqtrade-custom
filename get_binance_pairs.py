#!/usr/bin/env python3
"""快速获取币安USDT永续合约活跃币种"""
import ccxt
import json

# 初始化交易所
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897',
    }
})

print("正在获取币安USDT永续合约市场信息...")
markets = exchange.load_markets()

# 筛选USDT永续合约
usdt_futures = []
for symbol, market in markets.items():
    if (market.get('quote') == 'USDT' and
        market.get('type') == 'swap' and
        market.get('active', False)):
        # 转换为freqtrade格式: BTC/USDT:USDT
        base = market['base']
        usdt_futures.append(f"{base}/USDT:USDT")

# 按字母排序
usdt_futures.sort()

print(f"\n找到 {len(usdt_futures)} 个活跃的USDT永续合约:")
print("=" * 80)

for pair in usdt_futures:
    print(pair)

# 保存到文件
with open('binance_usdt_futures.txt', 'w') as f:
    for pair in usdt_futures:
        f.write(pair + '\n')

print(f"\n✅ 列表已保存到: binance_usdt_futures.txt")
