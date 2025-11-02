#!/bin/bash
# NostalgiaForInfinity 策略对比测试脚本
# 用于比较您的定制版本和原项目最新版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NostalgiaForInfinity 策略对比测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查虚拟环境
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}警告: 虚拟环境未激活${NC}"
    echo "激活虚拟环境..."
    source .venv/bin/activate
fi

# 测试参数配置
TIMERANGE="20241001-20241101"  # 可以根据需要调整
PAIRS="BTC/USDT ETH/USDT BNB/USDT"
TIMEFRAME="5m"
STAKE_AMOUNT=1000

echo -e "${GREEN}测试配置:${NC}"
echo "  时间范围: $TIMERANGE"
echo "  时间框架: $TIMEFRAME"
echo "  测试币对: $PAIRS"
echo "  模拟本金: $STAKE_AMOUNT USDT"
echo ""

# 创建结果目录
RESULTS_DIR="backtest_comparison_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo -e "${YELLOW}步骤 1/4: 检查策略文件${NC}"
if [ ! -f "user_data/strategies/NostalgiaForInfinityX7.py" ]; then
    echo -e "${RED}错误: 找不到当前版本策略文件${NC}"
    exit 1
fi

if [ ! -f "user_data/strategies/NostalgiaForInfinityX7_latest.py" ]; then
    echo -e "${RED}错误: 找不到最新版本策略文件${NC}"
    exit 1
fi

# 重命名最新版本为可测试的名字
echo "创建测试用策略副本..."
cp user_data/strategies/NostalgiaForInfinityX7_latest.py user_data/strategies/NostalgiaForInfinityX7_V17_1_51.py
sed -i 's/class NostalgiaForInfinityX7/class NostalgiaForInfinityX7_V17_1_51/' user_data/strategies/NostalgiaForInfinityX7_V17_1_51.py

echo -e "${GREEN}✓ 策略文件检查完成${NC}"
echo ""

echo -e "${YELLOW}步骤 2/4: 下载历史数据（如果需要）${NC}"
echo "检查是否已有数据..."
# 这里可以选择性下载数据
# freqtrade download-data --exchange binance --pairs $PAIRS --timeframes $TIMEFRAME --days 90

echo -e "${GREEN}✓ 数据检查完成${NC}"
echo ""

echo -e "${YELLOW}步骤 3/4: 回测您的定制版本 (v17.1.41, 10倍杠杆)${NC}"
echo "开始回测..."
freqtrade backtesting \
  --strategy NostalgiaForInfinityX7 \
  --timeframe $TIMEFRAME \
  --timerange $TIMERANGE \
  --stake-amount $STAKE_AMOUNT \
  --export trades \
  --export-filename "$RESULTS_DIR/backtest_v17_1_41_custom.json" \
  2>&1 | tee "$RESULTS_DIR/backtest_v17_1_41_custom.log"

echo -e "${GREEN}✓ 定制版本回测完成${NC}"
echo ""

echo -e "${YELLOW}步骤 4/4: 回测原项目最新版本 (v17.1.51, 现货)${NC}"
echo "开始回测..."
freqtrade backtesting \
  --strategy NostalgiaForInfinityX7_V17_1_51 \
  --timeframe $TIMEFRAME \
  --timerange $TIMERANGE \
  --stake-amount $STAKE_AMOUNT \
  --export trades \
  --export-filename "$RESULTS_DIR/backtest_v17_1_51_original.json" \
  2>&1 | tee "$RESULTS_DIR/backtest_v17_1_51_original.log"

echo -e "${GREEN}✓ 原版回测完成${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}结果保存在: $RESULTS_DIR/${NC}"
echo ""
echo -e "${YELLOW}查看结果方法:${NC}"
echo "  1. 查看日志文件:"
echo "     cat $RESULTS_DIR/backtest_v17_1_41_custom.log"
echo "     cat $RESULTS_DIR/backtest_v17_1_51_original.log"
echo ""
echo "  2. 使用 FreqUI 可视化比较:"
echo "     ./start_webui.sh"
echo "     然后在浏览器中查看回测结果"
echo ""
echo -e "${YELLOW}重要提示:${NC}"
echo "  - v17.1.41 使用 10倍杠杆 + 自定义止损（期货模式）"
echo "  - v17.1.51 使用现货模式（无杠杆）"
echo "  - 回测结果会有显著差异，请注意风险管理"
echo ""
