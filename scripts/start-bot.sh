#!/bin/bash

################################################################################
# Freqtrade Bot 启动脚本
#
# 功能：
# - 启动 Freqtrade 交易 Bot
# - 支持自定义配置文件和策略
# - 自动处理端口冲突
# - 支持前台/后台运行
################################################################################

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 加载共享函数库
source "${SCRIPT_DIR}/lib/common.sh"

# 默认配置
DEFAULT_CONFIG="${SCRIPT_DIR}/user_data/config-custom.json"
PRIVATE_CONFIG="${SCRIPT_DIR}/user_data/config-private.json"
DEFAULT_STRATEGY="NostalgiaForInfinityX7"  # 默认策略
CONFIG_FILE=""
STRATEGY=""
DAEMON_MODE=false
LOG_FILE="${SCRIPT_DIR}/user_data/logs/freqtrade.log"

################################################################################
# 帮助信息
################################################################################

show_help() {
    cat << EOF
Freqtrade Bot 启动脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -c, --config FILE       指定主配置文件（默认: user_data/config-custom.json）
    -s, --strategy NAME     指定策略名称（覆盖配置文件中的策略）
    -d, --daemon            后台运行模式
    --stop                  停止运行中的 Bot

配置文件加载顺序:
    1. 主配置文件（-c 指定或默认 config-custom.json）
    2. 私有配置文件（user_data/config-private.json，如果存在）

示例:
    $0                                          # 使用默认配置启动
    $0 -c user_data/config.json                 # 使用指定配置文件
    $0 -s NostalgiaForInfinityX7                # 使用指定策略
    $0 -c user_data/config.json -s MyStrategy   # 同时指定配置和策略
    $0 -d                                       # 后台运行
    $0 --stop                                   # 停止 Bot

EOF
    exit 0
}

################################################################################
# 停止 Bot
################################################################################

stop_bot() {
    print_header "停止 Freqtrade Bot"

    local pids
    pids=$(find_bot_process)

    if [ -z "$pids" ]; then
        print_info "Freqtrade Bot 未运行"
        exit 0
    fi

    print_info "找到以下 Bot 进程："
    ps aux | grep "freqtrade trade" | grep -v grep || true
    echo ""

    for pid in $pids; do
        stop_process_gracefully "$pid"
    done

    print_success "Freqtrade Bot 已停止"
    exit 0
}

################################################################################
# 启动 Bot
################################################################################

start_bot() {
    print_header "Freqtrade Bot 启动脚本"

    # 步骤 1: 检查依赖
    print_info "步骤 1/5: 检查依赖..."

    if ! check_venv; then
        exit 1
    fi

    if ! check_freqtrade_command; then
        exit 1
    fi

    # 确定使用的配置文件
    if [ -z "$CONFIG_FILE" ]; then
        CONFIG_FILE="$DEFAULT_CONFIG"
    fi

    if ! check_config_file "$CONFIG_FILE"; then
        print_info "使用: freqtrade new-config --config $CONFIG_FILE 创建配置文件"
        exit 1
    fi

    print_success "依赖检查通过"

    # 步骤 2: 检查端口占用
    print_info "步骤 2/5: 检查端口 $BOT_PORT..."

    if check_port $BOT_PORT; then
        print_warning "端口 $BOT_PORT 已被占用，尝试清理..."
        kill_port_process $BOT_PORT "freqtrade"

        if ! wait_port_ready $BOT_PORT 10; then
            print_error "端口 $BOT_PORT 无法释放，请手动检查"
            exit 1
        fi
    else
        print_success "端口 $BOT_PORT 可用"
    fi

    # 步骤 3: 设置代理（如果需要）
    print_info "步骤 3/5: 配置环境..."
    export https_proxy=http://127.0.0.1:7897
    export http_proxy=http://127.0.0.1:7897
    print_success "环境配置完成"

    # 步骤 4: 构建启动命令
    print_info "步骤 4/5: 准备启动命令..."

    local freqtrade_bin="${VENV_PATH}/bin/freqtrade"
    local cmd_array=("$freqtrade_bin" "trade" "--config" "$CONFIG_FILE")

    # 如果 config-private.json 存在，也加载它
    if [ -f "$PRIVATE_CONFIG" ]; then
        cmd_array+=("--config" "$PRIVATE_CONFIG")
        print_info "私有配置: $PRIVATE_CONFIG"
    fi

    # 添加策略（用户指定的或默认策略）
    local strategy_to_use="${STRATEGY:-$DEFAULT_STRATEGY}"
    if [ -n "$strategy_to_use" ]; then
        cmd_array+=("--strategy" "$strategy_to_use")
    fi

    print_info "主配置文件: $CONFIG_FILE"
    if [ -n "$strategy_to_use" ]; then
        print_info "策略: $strategy_to_use"
    fi
    print_success "启动命令准备完成"

    # 步骤 5: 启动 Bot
    print_info "步骤 5/5: 启动 Freqtrade Bot..."
    echo ""

    if [ "$DAEMON_MODE" = true ]; then
        # 后台模式
        print_info "后台模式启动..."
        nohup "${cmd_array[@]}" >> "$LOG_FILE" 2>&1 &
        local pid=$!
        sleep 3

        # 检查进程是否还在运行
        if ! kill -0 "$pid" 2>/dev/null; then
            print_error "Bot 启动失败，查看日志: $LOG_FILE"
            tail -20 "$LOG_FILE"
            exit 1
        fi

        # 等待 API 就绪
        print_info "等待 Bot API 就绪..."
        local count=0
        while [ $count -lt 15 ]; do
            if check_bot_health; then
                break
            fi
            sleep 1
            count=$((count + 1))
        done

        print_separator
        print_success "Freqtrade Bot 已启动！"
        echo ""
        echo "  🤖 进程 ID:    $pid"
        echo "  🔗 API 地址:   http://127.0.0.1:$BOT_PORT"
        echo "  📊 日志文件:   $LOG_FILE"
        echo ""
        if command -v cmd.exe > /dev/null 2>&1; then
            # WSL 环境提示
            print_info "💡 在 Windows 上可通过 http://127.0.0.1:$BOT_PORT 访问 Bot API"
            echo ""
        fi
        echo "  查看日志:     tail -f $LOG_FILE"
        echo "  停止服务:     $0 --stop"
        print_separator
        echo ""

    else
        # 前台模式
        print_info "前台模式启动..."
        print_success "Bot 正在启动..."
        print_info "按 Ctrl+C 停止服务"
        echo ""
        print_separator
        echo ""
        exec "${cmd_array[@]}"
    fi
}

################################################################################
# 主程序
################################################################################

# 解析命令行参数
ACTION="start"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -s|--strategy)
            STRATEGY="$2"
            shift 2
            ;;
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        *)
            print_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 执行操作
case $ACTION in
    stop)
        stop_bot
        ;;
    start)
        start_bot
        ;;
esac
