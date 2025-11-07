#!/bin/bash

# 快速查看反转分析结果
# 在浏览器中打开最新的HTML文件

cd /home/dministrator/Newproject/freqtrade

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  查找生成的反转分析结果..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查结果目录
if [ ! -d "user_data/reversal_results" ]; then
    echo "❌ 错误：找不到结果目录 user_data/reversal_results"
    echo "   请先运行: python scripts/analyze_reversals.py --pairs BTC/USDT:USDT"
    exit 1
fi

# 统计文件
html_count=$(ls user_data/reversal_results/*.html 2>/dev/null | wc -l)

if [ "$html_count" -eq 0 ]; then
    echo "❌ 错误：没有找到任何HTML结果文件"
    echo "   请先运行: python scripts/analyze_reversals.py --pairs BTC/USDT:USDT"
    exit 1
fi

echo "找到 $html_count 个HTML结果文件："
echo ""
ls -lth user_data/reversal_results/*.html | head -10
echo ""

# 获取最新的HTML文件
latest_html=$(ls -t user_data/reversal_results/*.html | head -1)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  在浏览器中打开最新结果："
echo "  $(basename "$latest_html")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 转换为Windows路径
windows_path=$(wslpath -w "$latest_html")

# 在Windows浏览器中打开
cmd.exe /c start "$windows_path"

echo "✓ 已在浏览器中打开！"
echo ""
echo "如需查看其他文件，请手动打开："
echo "  user_data/reversal_results/"
echo ""
