#!/bin/bash
# 分批下载49个新币种数据
# 每批8个币种，共6批

source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

echo "=========================================="
echo "开始分批下载49个新币种数据"
echo "时间范围: 20250501-20251108"
echo "时间周期: 5m 15m 1h 4h 1d"
echo "=========================================="

# 批次1 (8个币种)
echo ""
echo "[批次 1/6] 下载: 1INCH ACT AERO AI AIXBT ANKR BAND BRETT"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs 1INCH/USDT:USDT ACT/USDT:USDT AERO/USDT:USDT AI/USDT:USDT AIXBT/USDT:USDT ANKR/USDT:USDT BAND/USDT:USDT BRETT/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo "批次1完成，等待5秒..."
sleep 5

# 批次2 (8个币种)
echo ""
echo "[批次 2/6] 下载: CELO CETUS CHILLGUY COAI CYBER DUSK EGLD EIGEN"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs CELO/USDT:USDT CETUS/USDT:USDT CHILLGUY/USDT:USDT COAI/USDT:USDT CYBER/USDT:USDT DUSK/USDT:USDT EGLD/USDT:USDT EIGEN/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo "批次2完成，等待5秒..."
sleep 5

# 批次3 (8个币种)
echo ""
echo "[批次 3/6] 下载: ENA ENS ETHFI FARTCOIN FLOW FLUID FXS GOAT"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs ENA/USDT:USDT ENS/USDT:USDT ETHFI/USDT:USDT FARTCOIN/USDT:USDT FLOW/USDT:USDT FLUID/USDT:USDT FXS/USDT:USDT GOAT/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo "批次3完成，等待5秒..."
sleep 5

# 批次4 (8个币种)
echo ""
echo "[批次 4/6] 下载: GRT HIGH HOOK ICP JTO JUP KAIA KAS"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs GRT/USDT:USDT HIGH/USDT:USDT HOOK/USDT:USDT ICP/USDT:USDT JTO/USDT:USDT JUP/USDT:USDT KAIA/USDT:USDT KAS/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo "批次4完成，等待5秒..."
sleep 5

# 批次5 (8个币种)
echo ""
echo "[批次 5/6] 下载: LPT LQTY METIS MEW MINA MOODENG MORPHO NAORIS"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs LPT/USDT:USDT LQTY/USDT:USDT METIS/USDT:USDT MEW/USDT:USDT MINA/USDT:USDT MOODENG/USDT:USDT MORPHO/USDT:USDT NAORIS/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo "批次5完成，等待5秒..."
sleep 5

# 批次6 (8个币种 - 最后一批)
echo ""
echo "[批次 6/6] 下载: NEIRO PNUT PONKE POPCAT PUFFER QTUM RESOLV RONIN"
freqtrade download-data \
  --config config-download.json \
  --exchange binance \
  --pairs NEIRO/USDT:USDT PNUT/USDT:USDT PONKE/USDT:USDT POPCAT/USDT:USDT PUFFER/USDT:USDT QTUM/USDT:USDT RESOLV/USDT:USDT RONIN/USDT:USDT \
  --timeframes 5m 15m 1h 4h 1d \
  --timerange 20250501-20251108 \
  --trading-mode futures

echo ""
echo "=========================================="
echo "✅ 全部6批次下载完成！"
echo "=========================================="
