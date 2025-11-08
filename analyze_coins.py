#!/usr/bin/env python3
"""分析币种并生成候选垃圾币列表"""

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

# config-custom.json额外黑名单
config_blacklist = {'INJ', 'XRP', 'TRX', 'ALGO'}

# blacklist-binance.json中明确的币种（从正则中提取）
binance_blacklist_explicit = {
    'BNB',      # 交易所代币
    '1000PEPE', '1000SHIB',  # 1000系列
    'CHZ',      # 粉丝代币
    'USDC',     # 稳定币
    # 问题代币列表中的
    'MAGIC', 'GMX', 'NEAR', 'SOL', 'PENDLE', 'RUNE', 'AUCTION',
    'ENJ', 'GMT', 'KAVA', 'BLUR', 'AXS', 'BCH', 'HBAR', 'IMX',
    'MANA', 'TIA', 'ZK', 'HYPE'
}

print("=" * 80)
print("币种分析报告")
print("=" * 80)

print(f"\n1. 已下载币种总数: {len(downloaded_coins)}")
print(f"2. 已验证高质量币种: {len(high_quality_coins)}")
print(f"3. Config额外黑名单: {len(config_blacklist)}")
print(f"4. Binance主黑名单(已下载中): {len(binance_blacklist_explicit)}")

# 计算可用的垃圾币候选
all_excluded = high_quality_coins | config_blacklist | binance_blacklist_explicit
candidate_coins = downloaded_coins - all_excluded

print(f"\n总排除币种数: {len(all_excluded)}")
print(f"剩余垃圾币候选: {len(candidate_coins)}")

print("\n" + "=" * 80)
print("垃圾币候选列表 (需要回测的币种):")
print("=" * 80)
for coin in sorted(candidate_coins):
    print(f"  {coin}/USDT:USDT")

print("\n" + "=" * 80)
print("从黑名单中可恢复的优质币种建议:")
print("=" * 80)

# 推荐从黑名单恢复的币种
recommended_recovery = {
    'SOL': '主流Layer1公链',
    'NEAR': '主流Layer1公链',
    'PENDLE': 'DeFi收益代币化协议',
    'IMX': 'Layer2游戏生态',
    'HBAR': 'Hedera公链',
    'TIA': 'Celestia模块化区块链',
    'MANA': 'Decentraland元宇宙',
    'AXS': 'Axie Infinity游戏',
    'GMX': 'DeFi衍生品交易',
    'MAGIC': 'Treasure游戏生态',
    'BCH': '比特币现金',
    'BLUR': 'NFT市场',
    'KAVA': 'DeFi借贷平台',
    'RUNE': 'THORChain跨链',
    '1000PEPE': 'PEPE meme币(1000倍)',
    '1000SHIB': 'SHIB meme币(1000倍)',
}

blacklist_in_downloaded = binance_blacklist_explicit & downloaded_coins
recoverable = blacklist_in_downloaded - high_quality_coins - config_blacklist

print(f"\n可从黑名单恢复: {len(recoverable)} 个")
for coin in sorted(recoverable):
    desc = recommended_recovery.get(coin, '未知')
    print(f"  {coin}/USDT:USDT - {desc}")

# 计算恢复后的总数
total_after_recovery = len(candidate_coins) + len(recoverable)
print(f"\n恢复黑名单后总计: {total_after_recovery} 个币种")
print(f"还需补充: {max(0, 70 - total_after_recovery)} 个新币种\n")

# 生成配对列表文件
with open('/home/dministrator/Newproject/freqtrade/candidate_pairs.txt', 'w') as f:
    f.write("# 垃圾币候选列表 (用于回测识别)\n")
    f.write(f"# 生成时间: 2025-11-08\n")
    f.write(f"# 总计: {total_after_recovery} 个币种\n\n")

    f.write("## 1. 原始候选币种 (未在任何黑名单中)\n")
    for coin in sorted(candidate_coins):
        f.write(f"{coin}/USDT:USDT\n")

    f.write(f"\n## 2. 从黑名单恢复的币种 ({len(recoverable)}个)\n")
    for coin in sorted(recoverable):
        desc = recommended_recovery.get(coin, '')
        f.write(f"{coin}/USDT:USDT  # {desc}\n")

print(f"✅ 候选列表已保存到: candidate_pairs.txt")
