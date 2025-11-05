#!/bin/bash
# 策略探索工具 - 快速查看策略的不同部分

STRATEGY_FILE="user_data/strategies/NostalgiaForInfinityX7.py"

show_help() {
    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 NostalgiaForInfinityX7 策略探索工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用法: $0 <命令> [参数]

可用命令:

  config              显示策略的核心配置 (前300行)
  methods             显示所有方法列表
  method <名称>       显示特定方法的代码
  mode <模式名>       显示特定交易模式的相关代码
  indicators          显示指标计算部分
  entry               显示入场信号部分
  exit                显示出场信号部分
  search <关键词>     搜索包含关键词的代码
  line <起始> <结束>  显示特定行范围的代码

示例:

  $0 config                      # 查看配置
  $0 method populate_indicators  # 查看指标计算方法
  $0 mode long_normal            # 查看 long_normal 模式
  $0 search "stoploss"           # 搜索止损相关代码
  $0 line 1000 1100              # 查看 1000-1100 行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

show_config() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚙️  策略核心配置"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    head -n 300 "$STRATEGY_FILE" | nl -ba
}

show_methods() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 所有方法列表"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep -n "^\s*def " "$STRATEGY_FILE" | head -50
    echo ""
    echo "提示: 使用 '$0 method <方法名>' 查看具体方法的代码"
}

show_method() {
    local method_name="$1"
    if [ -z "$method_name" ]; then
        echo "❌ 错误: 请提供方法名"
        echo "用法: $0 method <方法名>"
        return 1
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 查找方法: $method_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 查找方法定义的行号
    local line_num=$(grep -n "def $method_name" "$STRATEGY_FILE" | head -1 | cut -d: -f1)

    if [ -z "$line_num" ]; then
        echo "❌ 未找到方法: $method_name"
        echo ""
        echo "相似的方法:"
        grep -n "def.*$method_name" "$STRATEGY_FILE" | head -5
        return 1
    fi

    echo "找到方法定义在第 $line_num 行"
    echo ""

    # 显示方法代码 (显示100行，通常足够看到一个方法)
    local end_line=$((line_num + 100))
    sed -n "${line_num},${end_line}p" "$STRATEGY_FILE" | nl -ba -v $line_num | head -100
    echo ""
    echo "提示: 如果代码被截断，使用 '$0 line $line_num $((line_num + 200))' 查看更多"
}

show_mode() {
    local mode_name="$1"
    if [ -z "$mode_name" ]; then
        echo "❌ 错误: 请提供模式名"
        echo "可用模式: long_normal, long_pump, long_quick, long_rebuy, long_rapid"
        echo "          short_normal, short_pump, short_quick"
        return 1
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎯 交易模式: $mode_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep -n "$mode_name" "$STRATEGY_FILE" | head -20
    echo ""
    echo "提示: 使用 '$0 search $mode_name' 查看所有相关代码"
}

show_indicators() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 指标计算方法"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    local line_num=$(grep -n "def populate_indicators" "$STRATEGY_FILE" | head -1 | cut -d: -f1)
    if [ -n "$line_num" ]; then
        echo "populate_indicators 方法在第 $line_num 行"
        echo ""
        sed -n "${line_num},$((line_num + 50))p" "$STRATEGY_FILE" | nl -ba -v $line_num
    fi
}

show_entry() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📈 入场信号方法"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    local line_num=$(grep -n "def populate_entry_trend" "$STRATEGY_FILE" | head -1 | cut -d: -f1)
    if [ -n "$line_num" ]; then
        echo "populate_entry_trend 方法在第 $line_num 行"
        echo ""
        sed -n "${line_num},$((line_num + 50))p" "$STRATEGY_FILE" | nl -ba -v $line_num
    fi
}

show_exit() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📉 出场信号方法"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    local line_num=$(grep -n "def populate_exit_trend" "$STRATEGY_FILE" | head -1 | cut -d: -f1)
    if [ -n "$line_num" ]; then
        echo "populate_exit_trend 方法在第 $line_num 行"
        echo ""
        sed -n "${line_num},$((line_num + 50))p" "$STRATEGY_FILE" | nl -ba -v $line_num
    fi
}

search_code() {
    local keyword="$1"
    if [ -z "$keyword" ]; then
        echo "❌ 错误: 请提供搜索关键词"
        return 1
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 搜索关键词: $keyword"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep -n "$keyword" "$STRATEGY_FILE" | head -30
    echo ""
    local count=$(grep -c "$keyword" "$STRATEGY_FILE")
    echo "共找到 $count 处匹配"
}

show_line_range() {
    local start="$1"
    local end="$2"

    if [ -z "$start" ] || [ -z "$end" ]; then
        echo "❌ 错误: 请提供起始和结束行号"
        echo "用法: $0 line <起始行> <结束行>"
        return 1
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 显示第 $start 到 $end 行"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sed -n "${start},${end}p" "$STRATEGY_FILE" | nl -ba -v $start
}

# 主程序
case "${1:-help}" in
    config)
        show_config
        ;;
    methods)
        show_methods
        ;;
    method)
        show_method "$2"
        ;;
    mode)
        show_mode "$2"
        ;;
    indicators)
        show_indicators
        ;;
    entry)
        show_entry
        ;;
    exit)
        show_exit
        ;;
    search)
        search_code "$2"
        ;;
    line)
        show_line_range "$2" "$3"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
