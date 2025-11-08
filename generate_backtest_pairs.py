#!/usr/bin/env python3
"""Generate pair list for backtest, excluding high-quality coins"""

import os
from pathlib import Path

# Get all coins with 5m data
data_dir = Path("user_data/data/binance/futures")
all_coins = set()
for file in data_dir.glob("*_USDT_USDT-5m-futures.feather"):
    coin = file.name.replace("_USDT_USDT-5m-futures.feather", "")
    all_coins.add(coin)

print(f"Total coins with data: {len(all_coins)}")

# High-quality coins to EXCLUDE
high_quality = {
    'CRV', 'GALA', 'ADA', 'LINK', 'SEI', 'AAVE', 'CAKE', 'DOGE', 'RENDER',
    'DYDX', 'FIL', 'APE', 'ETH', 'POL', 'UNI', 'AVAX', 'LDO', 'XLM',
    'ATOM', 'APT', 'PEOPLE', 'OP', 'DOT', 'LTC', 'SUI', 'ARB', 'WIF',
    'ETC', 'SAND', 'FET', 'WLD', 'SNX', 'COMP', 'SUSHI', 'CHZ'
}

print(f"High-quality coins to exclude: {len(high_quality)}")

# Calculate backtest candidates
backtest_coins = all_coins - high_quality
print(f"Backtest candidates: {len(backtest_coins)}")

# Sort for consistent output
backtest_coins_sorted = sorted(backtest_coins)

# Generate pairs in freqtrade format
pairs = [f"{coin}/USDT:USDT" for coin in backtest_coins_sorted]

# Save to file
output_file = "backtest_pairs.txt"
with open(output_file, 'w') as f:
    for pair in pairs:
        f.write(f"{pair}\n")

print(f"\nBacktest pairs saved to: {output_file}")
print(f"Total pairs for backtest: {len(pairs)}")

# Display first 10 and last 10 pairs
print("\nFirst 10 pairs:")
for pair in pairs[:10]:
    print(f"  {pair}")

print("\nLast 10 pairs:")
for pair in pairs[-10:]:
    print(f"  {pair}")

# Also save as space-separated for command line
pairs_cli = " ".join(pairs)
with open("backtest_pairs_cli.txt", 'w') as f:
    f.write(pairs_cli)

print(f"\nCLI format saved to: backtest_pairs_cli.txt")
