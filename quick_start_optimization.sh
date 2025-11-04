#!/bin/bash

# 策略优化快速开始脚本
# 创建日期: 2025-11-04

set -e  # 遇到错误立即退出

echo "=================================="
echo "策略优化快速开始脚本"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤1: 备份当前版本
echo -e "${YELLOW}[步骤 1/6] 备份当前版本...${NC}"
git add .
git commit -m "backup: before optimization - baseline performance" || echo "没有需要提交的更改"
git tag v1.0-baseline 2>/dev/null || echo "标签已存在"
echo -e "${GREEN}✓ 备份完成${NC}"
echo ""

# 步骤2: 创建优化分支
echo -e "${YELLOW}[步骤 2/6] 创建优化分支...${NC}"
git checkout -b feature/risk-optimization-phase1 2>/dev/null || git checkout feature/risk-optimization-phase1
echo -e "${GREEN}✓ 分支创建完成${NC}"
echo ""

# 步骤3: 创建优化配置文件
echo -e "${YELLOW}[步骤 3/6] 创建优化配置文件...${NC}"
if [ ! -f "user_data/config-optimized-v2-safe.json" ]; then
    cp user_data/config-backtest-nfx7-nogrind-55pairs.json \
       user_data/config-optimized-v2-safe.json
    echo -e "${GREEN}✓ 配置文件已创建: user_data/config-optimized-v2-safe.json${NC}"
else
    echo -e "${YELLOW}! 配置文件已存在，跳过创建${NC}"
fi
echo ""

# 步骤4: 修改杠杆参数
echo -e "${YELLOW}[步骤 4/6] 修改杠杆参数...${NC}"
echo "正在将杠杆从 10x 降低至 6x..."

# 使用 Python 修改 JSON 配置
python3 << 'EOF'
import json

config_file = "user_data/config-optimized-v2-safe.json"

with open(config_file, 'r') as f:
    config = json.load(f)

# 修改杠杆
config['trading_mode'] = 'futures'
config['margin_mode'] = 'isolated'

# 如果没有 leverage 字段，添加它
if 'leverage' not in config:
    config['leverage'] = 6
else:
    config['leverage'] = 6

# 限制最大开仓数
if 'max_open_trades' not in config:
    config['max_open_trades'] = 3
else:
    config['max_open_trades'] = 3

# 设置仓位管理
if 'stake_amount' not in config:
    config['stake_amount'] = 'unlimited'
if 'tradable_balance_ratio' not in config:
    config['tradable_balance_ratio'] = 0.33

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ 杠杆已修改为 6x")
print("✓ 最大开仓数设置为 3")
print("✓ 仓位比例设置为 33%")
EOF

echo -e "${GREEN}✓ 参数修改完成${NC}"
echo ""

# 步骤5: 创建优化策略副本
echo -e "${YELLOW}[步骤 5/6] 创建优化策略副本...${NC}"
if [ ! -f "user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py" ]; then
    cp user_data/strategies/NostalgiaForInfinityX7_NoGrind.py \
       user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py

    # 修改类名
    sed -i 's/class NostalgiaForInfinityX7_NoGrind(/class NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss(/g' \
        user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py

    echo -e "${GREEN}✓ 策略文件已创建: user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py${NC}"
else
    echo -e "${YELLOW}! 策略文件已存在，跳过创建${NC}"
fi
echo ""

# 步骤6: 显示下一步操作
echo -e "${YELLOW}[步骤 6/6] 准备运行回测...${NC}"
echo ""
echo "=================================="
echo -e "${GREEN}准备工作已完成！${NC}"
echo "=================================="
echo ""
echo "接下来需要手动完成以下步骤："
echo ""
echo "1. 编辑策略文件，修改止损参数："
echo "   文件: user_data/strategies/NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss.py"
echo ""
echo "   找到并修改以下参数："
echo -e "   ${YELLOW}stoploss = -0.99${NC}  →  ${GREEN}stoploss = -0.15${NC}"
echo ""
echo "   添加追踪止损（在 stoploss 下方添加）："
echo "   trailing_stop = True"
echo "   trailing_stop_positive = 0.01"
echo "   trailing_stop_positive_offset = 0.03"
echo "   trailing_only_offset_is_reached = True"
echo ""
echo "2. 运行对比回测："
echo ""
echo "   # 激活虚拟环境"
echo "   source .venv/bin/activate"
echo ""
echo "   # 运行回测"
echo "   freqtrade backtesting \\"
echo "     --config user_data/config-optimized-v2-safe.json \\"
echo "     --strategy NostalgiaForInfinityX7_NoGrind_v2_SafeStoploss \\"
echo "     --timerange 20241103-20251102 \\"
echo "     --breakdown day"
echo ""
echo "3. 对比结果："
echo "   - 爆仓次数应该 < 5次（原来50次）"
echo "   - 最大回撤应该 < -30%（原来-176%）"
echo "   - 总收益应该为正或亏损大幅减少"
echo ""
echo "=================================="
echo ""
echo "详细优化方案请查看："
echo "  - STRATEGY_OPTIMIZATION_PLAN.md"
echo "  - OPTIMIZATION_CHECKLIST.md"
echo ""
echo -e "${GREEN}祝优化顺利！🚀${NC}"
echo ""
