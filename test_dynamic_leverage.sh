#!/bin/bash
#
# 动态杠杆策略回测对比脚本
# 对比原版 vs 动态杠杆版本的效果
#

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   🧪 动态杠杆策略回测对比${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    echo -e "${YELLOW}📦 激活虚拟环境...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}❌ 错误: 找不到虚拟环境 (.venv)${NC}"
    exit 1
fi

# 检查策略文件是否存在
if [ ! -f "user_data/strategies/NostalgiaForInfinityX7.py" ]; then
    echo -e "${RED}❌ 错误: 找不到原版策略文件${NC}"
    exit 1
fi

if [ ! -f "user_data/strategies/NostalgiaForInfinityX7_DynamicLeverage.py" ]; then
    echo -e "${RED}❌ 错误: 找不到动态杠杆策略文件${NC}"
    exit 1
fi

# 设置回测参数
TIMERANGE="${1:-20240801-20241031}"  # 默认最近3个月
PAIRS=35  # 使用较少的交易对以加快速度

echo -e "${YELLOW}⚙️  回测参数:${NC}"
echo -e "  时间范围: ${TIMERANGE}"
echo -e "  交易对数: ${PAIRS} 对"
echo ""

# 创建结果目录
RESULT_DIR="backtest_results/dynamic_leverage_comparison"
mkdir -p "${RESULT_DIR}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 步骤 1/2: 回测原版策略 (10x 杠杆)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

freqtrade backtesting \
  --strategy NostalgiaForInfinityX7 \
  --timerange ${TIMERANGE} \
  --breakdown month \
  --export trades \
  --export-filename="${RESULT_DIR}/backtest_original.json" \
  2>&1 | tee "${RESULT_DIR}/backtest_original.log"

ORIGINAL_EXIT_CODE=$?

if [ $ORIGINAL_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ 原版策略回测失败！${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 原版策略回测完成${NC}"
echo ""
sleep 2

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 步骤 2/2: 回测动态杠杆策略 (高风险信号 3x)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

freqtrade backtesting \
  --strategy NostalgiaForInfinityX7_DynamicLeverage \
  --timerange ${TIMERANGE} \
  --breakdown month \
  --export trades \
  --export-filename="${RESULT_DIR}/backtest_dynamic.json" \
  2>&1 | tee "${RESULT_DIR}/backtest_dynamic.log"

DYNAMIC_EXIT_CODE=$?

if [ $DYNAMIC_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ 动态杠杆策略回测失败！${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 动态杠杆策略回测完成${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📈 回测结果对比${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}原版策略 (10x 杠杆):${NC}"
echo "────────────────────────────────────────────"
grep -A 30 "STRATEGY SUMMARY" "${RESULT_DIR}/backtest_original.log" | head -35 || echo "无法提取摘要"
echo ""

echo -e "${YELLOW}动态杠杆策略 (高风险信号 3x):${NC}"
echo "────────────────────────────────────────────"
grep -A 30 "STRATEGY SUMMARY" "${RESULT_DIR}/backtest_dynamic.log" | head -35 || echo "无法提取摘要"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 回测完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📁 结果文件保存在:${NC} ${RESULT_DIR}/"
echo ""
echo -e "${YELLOW}查看详细日志:${NC}"
echo "  cat ${RESULT_DIR}/backtest_original.log"
echo "  cat ${RESULT_DIR}/backtest_dynamic.log"
echo ""
echo -e "${YELLOW}分析交易记录:${NC}"
echo "  freqtrade backtesting-show -c ${RESULT_DIR}/backtest_original.json"
echo "  freqtrade backtesting-show -c ${RESULT_DIR}/backtest_dynamic.json"
echo ""
