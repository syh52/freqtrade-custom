#!/bin/bash

# Safe Backtesting Script - Prevents WSL Crashes
# This script uses optimized configuration with 40 pairs instead of 80

echo "========================================"
echo "  Safe Backtesting for NostalgiaForInfinityX7"
echo "  Using 40 pairs to prevent memory issues"
echo "========================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Check if timerange is provided
if [ -z "$1" ]; then
  echo "Usage: ./start_backtest_safe.sh TIMERANGE [STRATEGY]"
  echo "Example: ./start_backtest_safe.sh 20241001-20241101"
  echo "Example: ./start_backtest_safe.sh 20241001-20241101 NostalgiaForInfinityX7"
  echo ""
  echo "Using default timerange: last 30 days"
  TIMERANGE=""
else
  TIMERANGE="--timerange $1"
fi

# Check if strategy is provided
STRATEGY=${2:-NostalgiaForInfinityX7}

echo "Strategy: $STRATEGY"
echo "Config: config-backtest-optimized.json (40 pairs)"
echo ""

# Show memory usage before starting
echo "Memory status before backtest:"
free -h
echo ""

# Run backtest
freqtrade backtesting \
  --config user_data/config-backtest-optimized.json \
  --strategy $STRATEGY \
  $TIMERANGE \
  --breakdown month

echo ""
echo "========================================"
echo "  Backtest completed!"
echo "========================================"
echo ""

# Show memory usage after
echo "Memory status after backtest:"
free -h
