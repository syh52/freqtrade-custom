#!/bin/bash
#
# 策略快速查看工具
# 用法: ./view_strategy.sh [选项]

STRATEGY_FILE="user_data/strategies/NostalgiaForInfinityX7.py"
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}   📊 NostalgiaForInfinityX7 策略快速查看器${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

function show_menu() {
    echo -e "${YELLOW}请选择要查看的内容:${NC}"
    echo ""
    echo "  ${GREEN}基础信息${NC}"
    echo "    1) 查看核心配置参数"
    echo "    2) 查看版本和基本信息"
    echo "    3) 查看启用的入场信号列表"
    echo ""
    echo "  ${GREEN}入场信号${NC}"
    echo "    11) 查看信号 #1-#6 (Normal模式)"
    echo "    12) 查看信号 #41-#46 (Pump模式)"
    echo "    13) 查看信号 #61-#63 (Rebuy模式)"
    echo "    14) 查看信号 #101-#104 (High Profit模式)"
    echo "    15) 查看信号 #141-#145 (Grind模式)"
    echo "    16) 查看信号 #161-#163 (Top Coins模式)"
    echo "    17) 查看所有做空信号"
    echo "    18) 查看特定信号 (输入编号)"
    echo ""
    echo "  ${GREEN}出场和DCA${NC}"
    echo "    21) 查看自定义出场逻辑 (custom_exit)"
    echo "    22) 查看DCA加仓主逻辑"
    echo "    23) 查看Long Grind DCA"
    echo "    24) 查看出场条件方法列表"
    echo ""
    echo "  ${GREEN}技术指标${NC}"
    echo "    31) 查看populate_indicators (主指标)"
    echo "    32) 查看多时间框架指标方法"
    echo "    33) 查看BTC相关指标"
    echo ""
    echo "  ${GREEN}分析和文档${NC}"
    echo "    41) 生成策略结构报告"
    echo "    42) 打开完整概览文档"
    echo "    43) 搜索关键字"
    echo "    44) 查看方法定义位置"
    echo ""
    echo "  ${RED}0) 退出${NC}"
    echo ""
    echo -ne "${YELLOW}请输入选项: ${NC}"
}

function view_config() {
    echo -e "${GREEN}📋 核心配置参数:${NC}"
    echo ""
    sed -n '68,200p' "$STRATEGY_FILE" | grep -E "^\s+(stoploss|timeframe|minimal_roi|can_short|position_adjustment|max_entry|trailing)" | head -30
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_version() {
    echo -e "${GREEN}ℹ️ 策略版本信息:${NC}"
    echo ""
    sed -n '68,100p' "$STRATEGY_FILE" | head -20
    echo ""
    echo -e "${YELLOW}文件统计:${NC}"
    wc -l "$STRATEGY_FILE"
    du -h "$STRATEGY_FILE"
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_enabled_signals() {
    echo -e "${GREEN}✅ 已启用的入场信号:${NC}"
    echo ""
    echo -e "${BLUE}做多信号:${NC}"
    grep "long_entry_condition_.*_enable.*True" "$STRATEGY_FILE" | sed 's/.*long_entry_condition_/  #/' | sed 's/_enable.*//' | sort -n
    echo ""
    echo -e "${BLUE}做空信号:${NC}"
    grep "short_entry_condition_.*_enable.*True" "$STRATEGY_FILE" | sed 's/.*short_entry_condition_/  #/' | sed 's/_enable.*//' | sort -n
    echo ""
    echo -e "${RED}⏸️ 已禁用的信号:${NC}"
    grep "# .*entry_condition_.*enable" "$STRATEGY_FILE" | head -10
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_signal_range() {
    local start=$1
    local end=$2
    local title=$3

    echo -e "${GREEN}🎯 $title${NC}"
    echo ""

    for signal in $(seq $start $end); do
        line=$(grep -n "if long_entry_condition_index == $signal:" "$STRATEGY_FILE" | cut -d: -f1)
        if [ -n "$line" ]; then
            echo -e "${YELLOW}信号 #$signal (行 $line):${NC}"
            sed -n "${line},$((line+20))p" "$STRATEGY_FILE" | head -21
            echo ""
        fi
    done

    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_specific_signal() {
    echo -ne "${YELLOW}请输入信号编号 (例如: 142): ${NC}"
    read signal_num

    line=$(grep -n "if long_entry_condition_index == $signal_num:" "$STRATEGY_FILE" | cut -d: -f1)

    if [ -z "$line" ]; then
        # 尝试查找short信号
        line=$(grep -n "if short_entry_condition_index == $signal_num:" "$STRATEGY_FILE" | cut -d: -f1)
    fi

    if [ -n "$line" ]; then
        echo -e "${GREEN}📍 信号 #$signal_num (行 $line):${NC}"
        echo ""
        sed -n "${line},$((line+100))p" "$STRATEGY_FILE" | head -101
    else
        echo -e "${RED}❌ 未找到信号 #$signal_num${NC}"
    fi

    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_custom_exit() {
    echo -e "${GREEN}🚪 自定义出场逻辑 (custom_exit):${NC}"
    echo ""
    echo -e "${YELLOW}方法位置: 行 1700${NC}"
    echo ""
    sed -n '1700,1800p' "$STRATEGY_FILE"
    echo ""
    echo -e "${YELLOW}... (方法约499行,仅显示前100行)${NC}"
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_dca_logic() {
    echo -e "${GREEN}💰 DCA加仓主逻辑 (adjust_trade_position):${NC}"
    echo ""
    echo -e "${YELLOW}方法位置: 行 2401${NC}"
    echo ""
    sed -n '2401,2550p' "$STRATEGY_FILE"
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_grind_dca() {
    echo -e "${GREEN}⚙️ Long Grind DCA 方法:${NC}"
    echo ""
    echo "  • long_grind_adjust_trade_position_v2  (行 37134)"
    echo "  • long_grind_adjust_trade_position_v3  (行 39544)"
    echo "  • long_grind_adjust_trade_position     (行 40872)"
    echo ""
    echo -ne "${YELLOW}选择版本 (2/3/main) 或按Enter返回: ${NC}"
    read version

    case $version in
        2)
            sed -n '37134,37250p' "$STRATEGY_FILE"
            ;;
        3)
            sed -n '39544,39660p' "$STRATEGY_FILE"
            ;;
        main)
            sed -n '40872,40988p' "$STRATEGY_FILE"
            ;;
        *)
            return
            ;;
    esac

    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_exit_methods() {
    echo -e "${GREEN}🚪 所有出场方法:${NC}"
    echo ""
    grep -n "def.*exit" "$STRATEGY_FILE" | head -40
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_populate_indicators() {
    echo -e "${GREEN}📊 populate_indicators 方法头部:${NC}"
    echo ""
    echo -e "${YELLOW}方法位置: 行 3763 (约8000行)${NC}"
    echo ""
    sed -n '3763,3900p' "$STRATEGY_FILE"
    echo ""
    echo -e "${YELLOW}... (仅显示前137行,方法包含大量技术指标计算)${NC}"
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_informative_methods() {
    echo -e "${GREEN}🕐 多时间框架指标方法:${NC}"
    echo ""
    grep -n "def informative_" "$STRATEGY_FILE"
    echo ""
    echo -ne "${YELLOW}选择时间框架 (1d/4h/1h/15m) 或按Enter返回: ${NC}"
    read tf

    case $tf in
        1d)
            sed -n '2870,3000p' "$STRATEGY_FILE" | head -50
            ;;
        4h)
            sed -n '2998,3100p' "$STRATEGY_FILE" | head -50
            ;;
        1h)
            sed -n '3169,3270p' "$STRATEGY_FILE" | head -50
            ;;
        15m)
            sed -n '3337,3438p' "$STRATEGY_FILE" | head -50
            ;;
        *)
            return
            ;;
    esac

    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function generate_report() {
    echo -e "${GREEN}📄 生成策略结构报告...${NC}"
    echo ""
    python analyze_strategy.py report
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function open_overview() {
    if [ -f "STRATEGY_OVERVIEW_COMPLETE.md" ]; then
        echo -e "${GREEN}📖 显示完整概览文档...${NC}"
        echo ""
        if command -v bat &> /dev/null; then
            bat STRATEGY_OVERVIEW_COMPLETE.md
        elif command -v less &> /dev/null; then
            less STRATEGY_OVERVIEW_COMPLETE.md
        else
            cat STRATEGY_OVERVIEW_COMPLETE.md
        fi
    else
        echo -e "${RED}❌ 未找到 STRATEGY_OVERVIEW_COMPLETE.md${NC}"
        echo -e "${YELLOW}正在生成...${NC}"
        python analyze_strategy.py markdown
        echo ""
    fi
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function search_keyword() {
    echo -ne "${YELLOW}请输入要搜索的关键字: ${NC}"
    read keyword

    echo -e "${GREEN}🔍 搜索结果:${NC}"
    echo ""
    grep -n "$keyword" "$STRATEGY_FILE" | head -50
    echo ""
    echo -e "${YELLOW}(仅显示前50个结果)${NC}"
    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

function view_method_location() {
    echo -ne "${YELLOW}请输入方法名 (例如: custom_stake_amount): ${NC}"
    read method

    echo -e "${GREEN}📍 方法位置:${NC}"
    echo ""
    line=$(grep -n "def $method" "$STRATEGY_FILE" | cut -d: -f1)

    if [ -n "$line" ]; then
        echo -e "${GREEN}找到: $method (行 $line)${NC}"
        echo ""
        sed -n "${line},$((line+50))p" "$STRATEGY_FILE"
    else
        echo -e "${RED}❌ 未找到方法: $method${NC}"
    fi

    echo ""
    echo -e "${YELLOW}按Enter返回菜单...${NC}"
    read
}

# 主循环
while true; do
    clear
    print_header
    show_menu
    read choice

    case $choice in
        1) view_config ;;
        2) view_version ;;
        3) view_enabled_signals ;;
        11) view_signal_range 1 6 "Normal模式信号 (#1-#6)" ;;
        12) view_signal_range 41 46 "Pump模式信号 (#41-#46)" ;;
        13) view_signal_range 61 63 "Rebuy模式信号 (#61-#63)" ;;
        14) view_signal_range 101 104 "High Profit模式信号 (#101-#104)" ;;
        15) view_signal_range 141 145 "Grind模式信号 (#141-#145)" ;;
        16) view_signal_range 161 163 "Top Coins模式信号 (#161-#163)" ;;
        17) view_signal_range 501 542 "做空信号 (#501-#542)" ;;
        18) view_specific_signal ;;
        21) view_custom_exit ;;
        22) view_dca_logic ;;
        23) view_grind_dca ;;
        24) view_exit_methods ;;
        31) view_populate_indicators ;;
        32) view_informative_methods ;;
        41) generate_report ;;
        42) open_overview ;;
        43) search_keyword ;;
        44) view_method_location ;;
        0)
            echo ""
            echo -e "${GREEN}👋 再见！${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}❌ 无效选项，请重新选择${NC}"
            sleep 2
            ;;
    esac
done
