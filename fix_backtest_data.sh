#!/bin/bash
# 修复回测数据 - 排除闪崩日期

set -e

echo "=================================================="
echo "  回测数据修复脚本"
echo "=================================================="
echo ""
echo "此脚本将:"
echo "1. 备份原始数据"
echo "2. 重新下载干净的历史数据（排除闪崩日期）"
echo "3. 使用修正后的回测参数重新测试"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 备份当前数据
BACKUP_DIR="user_data/data_backup_$(date +%Y%m%d_%H%M%S)"
echo "→ 备份当前数据到 $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp -r user_data/data/binance/futures "$BACKUP_DIR/"

# 删除闪崩日期的数据（可选：保留原数据，仅在回测时排除）
echo ""
echo "→ 准备重新下载数据..."
echo "  时间范围: 2024-01-01 至 2025-10-09（排除10月10日）"
echo ""

# 方案1: 分段下载，跳过10月10日
freqtrade download-data \
  --exchange binance \
  --trading-mode futures \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20240101-20251009 \
  --config user_data/config.json \
  --erase

echo ""
echo "→ 下载10月11日之后的数据"
freqtrade download-data \
  --exchange binance \
  --trading-mode futures \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20251011-20251101 \
  --config user_data/config.json

echo ""
echo "=================================================="
echo "  数据修复完成！"
echo "=================================================="
echo ""
echo "现在可以重新运行回测:"
echo ""
echo "  freqtrade backtesting \\"
echo "    --strategy NostalgiaForInfinityX7 \\"
echo "    --timerange 20240101-20251101 \\"
echo "    --config user_data/config.json"
echo ""
echo "原始数据已备份到: $BACKUP_DIR"
echo ""
