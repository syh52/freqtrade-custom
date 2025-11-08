#!/usr/bin/env python3
"""从币安列表中选择49个新币种"""

# 已下载的62个币种
downloaded_coins = {
    '1000PEPE', '1000SHIB', 'AAVE', 'ADA', 'ALGO', 'APE', 'APT', 'ARB',
    'ATOM', 'AVAX', 'AXS', 'BCH', 'BLUR', 'BNB', 'BTC', 'CAKE', 'CHZ',
    'COMP', 'CRV', 'DOGE', 'DOT', 'DYDX', 'ENJ', 'ETC', 'ETH', 'FET',
    'FIL', 'GALA', 'GMT', 'GMX', 'HBAR', 'HYPE', 'IMX', 'INJ', 'KAVA',
    'LDO', 'LINK', 'LTC', 'MAGIC', 'MANA', 'NEAR', 'OP', 'PENDLE',
    'PEOPLE', 'POL', 'RENDER', 'RUNE', 'SAND', 'SEI', 'SNX', 'SOL',
    'SUI', 'SUSHI', 'TIA', 'TRX', 'UNI', 'USDC', 'WIF', 'WLD', 'XLM',
    'XRP', 'ZK'
}

# 34个已验证高质量币种
high_quality_coins = {
    'CRV', 'GALA', 'ADA', 'LINK', 'SEI', 'AAVE', 'CAKE', 'DOGE',
    'RENDER', 'DYDX', 'FIL', 'APE', 'ETH', 'POL', 'UNI', 'AVAX',
    'LDO', 'XLM', 'ATOM', 'APT', 'PEOPLE', 'OP', 'DOT', 'LTC',
    'SUI', 'ARB', 'WIF', 'ETC', 'SAND', 'FET', 'WLD', 'SNX',
    'COMP', 'SUSHI', 'CHZ'
}

# Config额外黑名单
config_blacklist = {'INJ', 'XRP', 'TRX', 'ALGO'}

# 读取币安列表
with open('binance_usdt_futures.txt', 'r') as f:
    all_pairs = [line.strip() for line in f if line.strip()]

# 提取币种符号
all_coins = set()
for pair in all_pairs:
    if pair.endswith('/USDT:USDT'):
        coin = pair.replace('/USDT:USDT', '')
        all_coins.add(coin)

print(f"币安总计: {len(all_coins)} 个币种")
print(f"已下载: {len(downloaded_coins)} 个")
print(f"高质量(排除): {len(high_quality_coins)} 个")
print(f"额外黑名单: {len(config_blacklist)} 个")

# 排除已下载和高质量币种
exclude_set = downloaded_coins | high_quality_coins | config_blacklist
available_coins = all_coins - exclude_set

print(f"\n可选新币种: {len(available_coins)} 个")
print(f"需要选择: 49 个\n")

# 优先级分类（基于市值、流行度、新颖性）
tier1_coins = {
    # 主流Layer1/Layer2
    'TON', 'FTM', 'STRK', 'ICP', 'KAS', 'THETA', 'MINA', 'ROSE', 'EGLD',
    'FLOW', 'ZIL', 'QTUM', 'RONIN', 'METIS', 'KAIA', 'CELO', 'SKL',
    # 热门DeFi
    'AERO', 'MORPHO', 'PUFFER', 'USUAL', 'SWELL', 'FLUID', 'RESOLV',
    # 热门AI
    'AI', 'AIXBT', 'VIRTUAL', 'NAORIS', 'COAI',
    # 其他热门
    'PEPE', 'BONK', 'NEIRO', 'POPCAT', 'MEW', 'PNUT', 'GOAT', 'ACT',
    'FARTCOIN', 'CHILLGUY', 'MOODENG', 'BRETT', 'TURBO', 'PONKE',
}

tier2_coins = {
    # 中等市值项目
    '1INCH', 'BAND', 'ANKR', 'CELO', 'CETUS', 'CYBER', 'DUSK',
    'EIGEN', 'ENA', 'ENS', 'ETHFI', 'FXS', 'GRT', 'HIGH', 'HOOK',
    'JTO', 'JUP', 'LPT', 'LQTY', 'LSK', 'MASK', 'MAV', 'MEME',
    'MINA', 'MOVR', 'NFP', 'NMR', 'ONDO', 'ORDI', 'PYTH', 'QNT',
    'SAGA', 'SCR', 'SSV', 'STG', 'STX', 'TAO', 'THE', 'TNSR',
    'VANRY', 'VET', 'W', 'XTZ', 'YGG', 'ZEC', 'ZEN', 'ZETA', 'ZRO',
}

# 按优先级选择
selected = []

# 先从tier1选择（高优先级）
tier1_available = tier1_coins & available_coins
selected.extend(sorted(tier1_available)[:30])

# 再从tier2补充
if len(selected) < 49:
    tier2_available = tier2_coins & available_coins
    remaining = 49 - len(selected)
    selected.extend(sorted(tier2_available)[:remaining])

# 如果还不够，从剩余币种中补充
if len(selected) < 49:
    other_coins = available_coins - tier1_coins - tier2_coins
    remaining = 49 - len(selected)
    selected.extend(sorted(other_coins)[:remaining])

print("=" * 80)
print(f"已选择 {len(selected)} 个新币种:")
print("=" * 80)

# 按字母排序并输出
selected_sorted = sorted(selected)
for i, coin in enumerate(selected_sorted, 1):
    print(f"{i:2d}. {coin}/USDT:USDT")

# 保存到文件
with open('new_coins_to_download.txt', 'w') as f:
    for coin in selected_sorted:
        f.write(f"{coin}/USDT:USDT\n")

print(f"\n✅ 新币种列表已保存到: new_coins_to_download.txt")

# 生成下载命令
print("\n" + "=" * 80)
print("下载命令:")
print("=" * 80)
pairs_str = ' '.join([f"{coin}/USDT:USDT" for coin in selected_sorted])
print(f"""
source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

freqtrade download-data \\
  --exchange binance \\
  --pairs {pairs_str[:200]}... \\
  --timeframes 5m 15m 1h 4h 1d \\
  --timerange 20250501-20251108 \\
  --trading-mode futures \\
  --dataformat-ohlcv feather
""")

print("\n注意: 由于币种较多，命令被截断显示。请使用脚本生成的完整命令。")
