#!/bin/bash

# 反转点分析示例脚本
# 展示不同的使用场景

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  加密货币反转点分析 - 示例脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# ============================================================
# 示例 1: 基础用法 - 分析BTC最近一周数据
# ============================================================
echo "示例 1: 基础用法 - 分析BTC最近一周"
echo "命令: python scripts/analyze_reversals.py --pairs BTC/USDT:USDT --timerange 20241101-20241106 --methods fixed"
echo ""
read -p "按回车键运行示例 1..."

python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --timerange 20241101-20241106 \
  --methods fixed

echo ""
echo "✓ 示例 1 完成！查看生成的HTML文件。"
echo ""

# ============================================================
# 示例 2: 对比所有方法
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "示例 2: 对比所有三种检测方法"
echo "命令: python scripts/analyze_reversals.py --pairs BTC/USDT:USDT --methods all"
echo ""
read -p "按回车键运行示例 2..."

python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT \
  --timerange 20241101-20241106 \
  --methods all

echo ""
echo "✓ 示例 2 完成！对比三个HTML文件的差异。"
echo ""

# ============================================================
# 示例 3: 多个交易对批量分析
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "示例 3: 多个交易对批量分析"
echo "命令: python scripts/analyze_reversals.py --pairs BTC/USDT:USDT ETH/USDT:USDT"
echo ""
read -p "按回车键运行示例 3 (需要ETH数据)..."

python scripts/analyze_reversals.py \
  --pairs BTC/USDT:USDT ETH/USDT:USDT \
  --timerange 20241101-20241106 \
  --methods fixed

echo ""
echo "✓ 示例 3 完成！对比不同加密货币的反转模式。"
echo ""

# ============================================================
# 示例 4: 使用自定义配置文件
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "示例 4: 使用自定义配置文件"
echo "命令: python scripts/analyze_reversals.py --config user_data/reversal_config.json"
echo ""
read -p "按回车键运行示例 4..."

python scripts/analyze_reversals.py \
  --config user_data/reversal_config.json \
  --pairs BTC/USDT:USDT \
  --timerange 20241101-20241106

echo ""
echo "✓ 示例 4 完成！"
echo ""

# ============================================================
# 总结
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "所有示例完成！"
echo ""
echo "生成的文件位于: user_data/reversal_results/"
echo ""
echo "查看输出文件："
ls -lh user_data/reversal_results/ | tail -10
echo ""
echo "在浏览器中打开HTML文件即可查看交互式可视化。"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
