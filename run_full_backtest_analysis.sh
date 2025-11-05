#!/bin/bash
##############################################################################
# 完整的回测与最差交易分析流程
#
# 功能:
# 1. 下载历史K线数据 (可选)
# 2. 运行回测
# 3. 分析最差的交易
# 4. 生成可视化图表
##############################################################################

set -e  # 遇到错误时退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
STRATEGY="NostalgiaForInfinityX7"
CONFIG="config_backtest_futures.json"
TIMERANGE="20250101-20251001"
DATA_DIR="user_data/data/binance"
N_WORST_TRADES=20
N_DETAILED_ANALYSIS=5
N_VISUALIZE=10

# 币对列表 (前20个高流动性币对用于快速测试)
PAIRS_QUICK=(
    "BTC/USDT:USDT"
    "ETH/USDT:USDT"
    "BNB/USDT:USDT"
    "SOL/USDT:USDT"
    "XRP/USDT:USDT"
    "DOGE/USDT:USDT"
    "ADA/USDT:USDT"
    "TRX/USDT:USDT"
    "AVAX/USDT:USDT"
    "LINK/USDT:USDT"
    "DOT/USDT:USDT"
    "MATIC/USDT:USDT"
    "UNI/USDT:USDT"
    "LTC/USDT:USDT"
    "BCH/USDT:USDT"
    "ATOM/USDT:USDT"
    "ETC/USDT:USDT"
    "FIL/USDT:USDT"
    "APT/USDT:USDT"
    "ARB/USDT:USDT"
)

# 全部55个币对
PAIRS_ALL=(
    "BTC/USDT:USDT" "ETH/USDT:USDT" "BNB/USDT:USDT" "SOL/USDT:USDT" "XRP/USDT:USDT"
    "DOGE/USDT:USDT" "ADA/USDT:USDT" "TRX/USDT:USDT" "AVAX/USDT:USDT" "LINK/USDT:USDT"
    "DOT/USDT:USDT" "MATIC/USDT:USDT" "UNI/USDT:USDT" "LTC/USDT:USDT" "BCH/USDT:USDT"
    "ATOM/USDT:USDT" "ETC/USDT:USDT" "FIL/USDT:USDT" "APT/USDT:USDT" "ARB/USDT:USDT"
    "OP/USDT:USDT" "NEAR/USDT:USDT" "SUI/USDT:USDT" "INJ/USDT:USDT" "PEPE/USDT:USDT"
    "WIF/USDT:USDT" "SHIB/USDT:USDT" "FTM/USDT:USDT" "HBAR/USDT:USDT" "IMX/USDT:USDT"
    "AAVE/USDT:USDT" "GRT/USDT:USDT" "ALGO/USDT:USDT" "SAND/USDT:USDT" "MANA/USDT:USDT"
    "AXS/USDT:USDT" "RUNE/USDT:USDT" "FLR/USDT:USDT" "GALA/USDT:USDT" "APE/USDT:USDT"
    "CHZ/USDT:USDT" "ENJ/USDT:USDT" "THETA/USDT:USDT" "ZIL/USDT:USDT" "LDO/USDT:USDT"
    "CRV/USDT:USDT" "MKR/USDT:USDT" "SNX/USDT:USDT" "COMP/USDT:USDT" "SUSHI/USDT:USDT"
    "YFI/USDT:USDT" "1INCH/USDT:USDT" "BAL/USDT:USDT" "REN/USDT:USDT" "KNC/USDT:USDT"
)

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 激活虚拟环境
activate_venv() {
    if [ -d ".venv" ]; then
        print_step "Activating virtual environment..."
        source .venv/bin/activate
    else
        print_error "Virtual environment not found! Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
        exit 1
    fi
}

# 下载数据
download_data() {
    local mode=$1
    local pairs_var="PAIRS_${mode}"
    eval "pairs=(\"\${${pairs_var}[@]}\")"

    print_header "Step 1: Downloading Historical Data (${#pairs[@]} pairs)"

    local pairs_str="${pairs[*]}"

    print_step "Downloading data for timerange: $TIMERANGE"
    print_step "Timeframes: 5m, 15m, 1h, 4h, 1d"

    freqtrade download-data \
        --exchange binance \
        --trading-mode futures \
        --pairs $pairs_str \
        --timeframes 5m 15m 1h 4h 1d \
        --timerange $TIMERANGE \
        --config $CONFIG

    if [ $? -eq 0 ]; then
        print_step "✓ Data download completed"
    else
        print_warning "Data download failed or partially completed"
        echo "You can skip data download and use existing data by running: $0 --skip-download"
    fi
}

# 运行回测
run_backtest() {
    print_header "Step 2: Running Backtest"

    print_step "Strategy: $STRATEGY"
    print_step "Config: $CONFIG"
    print_step "Timerange: $TIMERANGE"

    freqtrade backtesting \
        --strategy $STRATEGY \
        --config $CONFIG \
        --timerange $TIMERANGE \
        --breakdown day \
        --export trades \
        --export-filename user_data/backtest_results/backtest_$(date +%Y%m%d_%H%M%S).json

    if [ $? -eq 0 ]; then
        print_step "✓ Backtest completed"
    else
        print_error "Backtest failed!"
        exit 1
    fi
}

# 分析最差交易
analyze_worst_trades() {
    print_header "Step 3: Analyzing Worst Trades"

    # 查找最新的回测结果
    LATEST_BACKTEST=$(ls -t user_data/backtest_results/*.json 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKTEST" ]; then
        print_error "No backtest results found!"
        exit 1
    fi

    print_step "Analyzing: $LATEST_BACKTEST"
    print_step "Number of worst trades to analyze: $N_WORST_TRADES"
    print_step "Detailed analysis for: $N_DETAILED_ANALYSIS trades"

    python3 analyze_worst_trades.py \
        --backtest-results "$LATEST_BACKTEST" \
        --data-dir "$DATA_DIR" \
        --n-worst $N_WORST_TRADES \
        --n-detailed $N_DETAILED_ANALYSIS

    if [ $? -eq 0 ]; then
        print_step "✓ Analysis completed"
    else
        print_error "Analysis failed!"
        exit 1
    fi
}

# 生成可视化图表
generate_visualizations() {
    print_header "Step 4: Generating Visualizations"

    # 查找最新的回测结果
    LATEST_BACKTEST=$(ls -t user_data/backtest_results/*.json 2>/dev/null | head -1)

    if [ -z "$LATEST_BACKTEST" ]; then
        print_error "No backtest results found!"
        exit 1
    fi

    print_step "Generating charts for: $LATEST_BACKTEST"
    print_step "Number of trades to visualize: $N_VISUALIZE"

    python3 visualize_worst_trades.py \
        --backtest-results "$LATEST_BACKTEST" \
        --data-dir "$DATA_DIR" \
        --output-dir "user_data/plot" \
        --n-worst $N_VISUALIZE

    if [ $? -eq 0 ]; then
        print_step "✓ Visualizations completed"
        print_step "Charts saved to: user_data/plot/"
    else
        print_warning "Visualization failed (may be due to missing matplotlib or data)"
    fi
}

# 显示摘要
show_summary() {
    print_header "Analysis Complete!"

    echo ""
    echo -e "${GREEN}Results and outputs:${NC}"
    echo "  • Backtest results: user_data/backtest_results/"
    echo "  • Analysis reports: user_data/backtest_results/*_analysis_*.json"
    echo "  • Charts: user_data/plot/"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "  1. Review the analysis report for optimization suggestions"
    echo "  2. Check the visualizations to understand trade behavior"
    echo "  3. Consider implementing the suggested strategy improvements"
    echo "  4. Re-run backtest with optimized parameters"
    echo ""
}

# 主流程
main() {
    local skip_download=false
    local quick_mode=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-download)
                skip_download=true
                shift
                ;;
            --quick)
                quick_mode=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-download    Skip data download step (use existing data)"
                echo "  --quick            Quick mode: only test with 20 pairs instead of 55"
                echo "  --help, -h         Show this help message"
                echo ""
                echo "Example:"
                echo "  $0                 # Full analysis with all 55 pairs"
                echo "  $0 --quick         # Quick test with 20 pairs"
                echo "  $0 --skip-download # Skip download, use existing data"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    print_header "Freqtrade Backtest & Worst Trades Analysis"
    echo ""
    echo "Configuration:"
    echo "  Strategy: $STRATEGY"
    echo "  Config: $CONFIG"
    echo "  Timerange: $TIMERANGE"
    if [ "$quick_mode" = true ]; then
        echo "  Mode: Quick (20 pairs)"
    else
        echo "  Mode: Full (55 pairs)"
    fi
    echo ""

    # 激活虚拟环境
    activate_venv

    # 下载数据 (可选)
    if [ "$skip_download" = false ]; then
        if [ "$quick_mode" = true ]; then
            download_data "QUICK"
        else
            download_data "ALL"
        fi
    else
        print_warning "Skipping data download as requested"
    fi

    # 运行回测
    run_backtest

    # 分析最差交易
    analyze_worst_trades

    # 生成可视化 (可选，如果失败不影响主流程)
    generate_visualizations || print_warning "Skipping visualization due to errors"

    # 显示摘要
    show_summary
}

# 运行主流程
main "$@"
