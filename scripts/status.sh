#!/bin/bash

################################################################################
# Freqtrade 服务状态查询脚本
#
# 功能：
# - 显示 Freqtrade Bot 运行状态
# - 显示 FreqUI 运行状态
# - 显示端口和健康状态
################################################################################

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 加载共享函数库
source "${SCRIPT_DIR}/lib/common.sh"

# 日志文件
BOT_LOG="${SCRIPT_DIR}/user_data/logs/freqtrade.log"
UI_LOG="/tmp/frequi.log"

################################################################################
# 显示 Bot 状态
################################################################################

show_bot_status() {
    echo "🤖 Freqtrade Bot"
    echo "─────────────────────────────────────────────────────"

    local pids
    pids=$(find_bot_process)

    if [ -z "$pids" ]; then
        echo "  状态:        ❌ 未运行"
    else
        echo "  状态:        ✅ 运行中"
        echo "  进程 ID:     $pids"

        # 显示端口监听状态
        if check_port $BOT_PORT; then
            echo "  端口:        $BOT_PORT (监听中)"
        else
            echo "  端口:        $BOT_PORT (未监听)"
        fi

        # 显示健康状态
        if check_bot_health; then
            echo "  健康检查:    ✅ 正常"
            echo "  API 地址:    http://127.0.0.1:$BOT_PORT"
        else
            echo "  健康检查:    ⚠️  API 未响应"
        fi

        # 显示进程详情
        echo ""
        echo "  进程详情:"
        ps aux | grep "freqtrade trade" | grep -v grep | awk '{printf "    PID: %-6s CPU: %-4s MEM: %-4s CMD: %s\n", $2, $3"%", $4"%", substr($0, index($0,$11))}'
    fi

    # 显示最近日志
    if [ -f "$BOT_LOG" ]; then
        echo ""
        echo "  最近日志 (最后 5 行):"
        tail -n 5 "$BOT_LOG" | sed 's/^/    /'
        echo ""
        echo "  完整日志:    tail -f $BOT_LOG"
    fi

    echo ""
}

################################################################################
# 显示 UI 状态
################################################################################

show_ui_status() {
    echo "📱 FreqUI"
    echo "─────────────────────────────────────────────────────"

    local pids
    pids=$(find_ui_process)

    if [ -z "$pids" ]; then
        echo "  状态:        ❌ 未运行"
    else
        echo "  状态:        ✅ 运行中"
        echo "  进程 ID:     $pids"

        # 显示端口监听状态
        if check_port $UI_PORT; then
            echo "  端口:        $UI_PORT (监听中)"
        else
            echo "  端口:        $UI_PORT (未监听)"
        fi

        # 显示健康状态
        if check_ui_health; then
            echo "  健康检查:    ✅ 正常"
            echo "  访问地址:    http://127.0.0.1:$UI_PORT"
        else
            echo "  健康检查:    ⚠️  服务未响应（可能正在启动）"
        fi

        # 显示进程详情
        echo ""
        echo "  进程详情:"
        ps aux | grep -E "vite.*frequi|npm.*dev" | grep -v grep | awk '{printf "    PID: %-6s CPU: %-4s MEM: %-4s CMD: %s\n", $2, $3"%", $4"%", substr($0, index($0,$11))}'
    fi

    # 显示最近日志
    if [ -f "$UI_LOG" ]; then
        echo ""
        echo "  最近日志 (最后 5 行):"
        tail -n 5 "$UI_LOG" | sed 's/^/    /'
        echo ""
        echo "  完整日志:    tail -f $UI_LOG"
    fi

    echo ""
}

################################################################################
# 显示连接信息
################################################################################

show_connection_info() {
    local bot_running=$(find_bot_process)
    local ui_running=$(find_ui_process)

    if [ -n "$bot_running" ] && [ -n "$ui_running" ]; then
        echo "🔗 连接信息"
        echo "─────────────────────────────────────────────────────"
        echo "  在 FreqUI 中连接 Bot："
        echo ""
        echo "  Bot 名称:    实盘Bot (任意)"
        echo "  API 地址:    http://127.0.0.1:$BOT_PORT"
        echo "  用户名:      freqtrade_user"
        echo "  密码:        freqtrade_pass123"
        echo ""
    fi
}

################################################################################
# 显示快捷命令
################################################################################

show_quick_commands() {
    echo "⚡ 快捷命令"
    echo "─────────────────────────────────────────────────────"
    echo "  启动所有服务:    ./ft start --bot --ui"
    echo "  只启动 Bot:      ./ft start --bot"
    echo "  只启动 UI:       ./ft start --ui"
    echo "  停止所有服务:    ./ft stop --all"
    echo "  查看状态:        ./ft status"
    echo ""
}

################################################################################
# 主程序
################################################################################

print_header "Freqtrade 服务状态"

# 显示 Bot 状态
show_bot_status

# 显示 UI 状态
show_ui_status

# 显示连接信息
show_connection_info

# 显示快捷命令
show_quick_commands

print_separator
