#!/bin/bash
# Run backtest on 75 selected pairs with backtest-specific config

source .venv/bin/activate

# Read pairs from file
PAIRS=$(cat backtest_pairs_cli.txt)

echo "================================================================"
echo "Starting backtest on 75 pairs"
echo "================================================================"
echo "Time range: 20250501-20251108 (6 months)"
echo "Strategy: NostalgiaForInfinityX7"
echo "Config: user_data/config-backtest.json (no pairlist filters)"
echo "Pairs: 75 coins (110 total - 35 high-quality excluded)"
echo "================================================================"

freqtrade backtesting \
  --config user_data/config-backtest.json \
  --config user_data/config-private.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20250501-20251108 \
  --pairs $PAIRS \
  --timeframe 5m \
  2>&1 | tee backtest_output.log

echo ""
echo "================================================================"
echo "Backtest completed! Check backtest_output.log for results"
echo "================================================================"
