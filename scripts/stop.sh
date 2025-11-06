#!/bin/bash

################################################################################
# Freqtrade 服务停止脚本
#
# 功能：
# - 停止 Freqtrade Bot
# - 停止 FreqUI
# - 支持同时停止所有服务
################################################################################

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 加载共享函数库
source "${SCRIPT_DIR}/lib/common.sh"

# 默认停止所有服务
STOP_BOT=false
STOP_UI=false

################################################################################
# 帮助信息
################################################################################

show_help() {
    cat << EOF
Freqtrade 服务停止脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    --bot                   只停止 Bot
    --ui                    只停止 UI
    --all                   停止所有服务（默认）

示例:
    $0                      # 停止所有服务
    $0 --all                # 停止所有服务
    $0 --bot                # 只停止 Bot
    $0 --ui                 # 只停止 UI
    $0 --bot --ui           # 停止 Bot 和 UI

EOF
    exit 0
}

################################################################################
# 停止 Bot
################################################################################

stop_bot() {
    print_info "正在停止 Freqtrade Bot..."

    local pids
    pids=$(find_bot_process)

    if [ -z "$pids" ]; then
        print_info "Bot 未运行"
        return 0
    fi

    print_info "找到以下 Bot 进程："
    ps aux | grep "freqtrade trade" | grep -v grep || true
    echo ""

    for pid in $pids; do
        stop_process_gracefully "$pid"
    done

    print_success "Bot 已停止"
}

################################################################################
# 停止 UI
################################################################################

stop_ui() {
    print_info "正在停止 FreqUI..."

    local pids
    pids=$(find_ui_process)

    if [ -z "$pids" ]; then
        print_info "UI 未运行"
        return 0
    fi

    print_info "找到以下 UI 进程："
    ps aux | grep -E "vite.*frequi|npm.*dev" | grep -v grep || true
    echo ""

    for pid in $pids; do
        stop_process_gracefully "$pid"
    done

    print_success "UI 已停止"
}

################################################################################
# 主程序
################################################################################

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --bot)
            STOP_BOT=true
            shift
            ;;
        --ui)
            STOP_UI=true
            shift
            ;;
        --all)
            STOP_BOT=true
            STOP_UI=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 如果没有指定任何选项，默认停止所有服务
if [ "$STOP_BOT" = false ] && [ "$STOP_UI" = false ]; then
    STOP_BOT=true
    STOP_UI=true
fi

# 打印标题
print_header "Freqtrade 服务停止脚本"

# 停止服务
if [ "$STOP_BOT" = true ]; then
    stop_bot
fi

if [ "$STOP_UI" = true ]; then
    stop_ui
fi

echo ""
print_separator
print_success "所有指定的服务已停止"
print_separator
echo ""
