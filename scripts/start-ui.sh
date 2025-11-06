#!/bin/bash

################################################################################
# FreqUI 启动脚本
#
# 功能：
# - 启动 FreqUI Web 前端界面
# - 自动处理端口冲突
# - 支持前台/后台运行
# - 自动打开浏览器（可选）
################################################################################

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 加载共享函数库
source "${SCRIPT_DIR}/lib/common.sh"

# 配置
DAEMON_MODE=false
OPEN_BROWSER=true
LOG_FILE="/tmp/frequi.log"
FREQUI_URL="http://127.0.0.1:${UI_PORT}"
BOT_API_URL="http://127.0.0.1:${BOT_PORT}"

################################################################################
# 帮助信息
################################################################################

show_help() {
    cat << EOF
FreqUI 启动脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -d, --daemon            后台运行模式
    --no-browser            不自动打开浏览器
    --stop                  停止运行中的 FreqUI

示例:
    $0                      # 前台运行，自动打开浏览器
    $0 -d                   # 后台运行
    $0 --no-browser         # 不打开浏览器
    $0 --stop               # 停止 FreqUI

EOF
    exit 0
}

################################################################################
# 停止 FreqUI
################################################################################

stop_ui() {
    print_header "停止 FreqUI"

    local pids
    pids=$(find_ui_process)

    if [ -z "$pids" ]; then
        print_info "FreqUI 未运行"
        exit 0
    fi

    print_info "找到以下 FreqUI 进程："
    ps aux | grep -E "vite.*frequi|npm.*dev" | grep -v grep || true
    echo ""

    for pid in $pids; do
        stop_process_gracefully "$pid"
    done

    print_success "FreqUI 已停止"
    exit 0
}

################################################################################
# 启动 FreqUI
################################################################################

start_ui() {
    print_header "FreqUI 启动脚本"

    # 步骤 1: 检查 FreqUI 目录
    print_info "步骤 1/5: 检查 FreqUI 目录..."

    if ! check_frequi_dir; then
        print_info "FreqUI 目录: $FREQUI_DIR"
        exit 1
    fi

    print_success "FreqUI 目录存在"

    # 步骤 2: 检查依赖
    print_info "步骤 2/5: 检查依赖..."

    if [ ! -d "$FREQUI_DIR/node_modules" ]; then
        print_warning "依赖未安装，正在安装..."
        cd "$FREQUI_DIR"
        npm install
        if [ $? -ne 0 ]; then
            print_error "依赖安装失败"
            exit 1
        fi
    fi

    print_success "依赖检查通过"

    # 步骤 3: 检查端口占用
    print_info "步骤 3/5: 检查端口 $UI_PORT..."

    if check_port $UI_PORT; then
        print_warning "端口 $UI_PORT 已被占用，尝试清理..."
        kill_port_process $UI_PORT "vite|npm"

        if ! wait_port_ready $UI_PORT 15; then
            print_error "端口 $UI_PORT 无法释放，请手动检查"
            exit 1
        fi
    else
        print_success "端口 $UI_PORT 可用"
    fi

    # 步骤 4: 启动 FreqUI
    print_info "步骤 4/5: 启动 FreqUI..."

    cd "$FREQUI_DIR"

    if [ "$DAEMON_MODE" = true ]; then
        # 后台模式
        print_info "后台模式启动..."
        nohup npm run dev > "$LOG_FILE" 2>&1 &
        local pid=$!
        sleep 5

        # 检查进程是否还在运行
        if ! kill -0 "$pid" 2>/dev/null; then
            print_error "FreqUI 启动失败，查看日志: $LOG_FILE"
            tail -20 "$LOG_FILE"
            exit 1
        fi

        # 等待服务就绪
        print_info "等待 FreqUI 就绪..."
        local count=0
        while [ $count -lt 20 ]; do
            if check_ui_health; then
                break
            fi
            sleep 1
            count=$((count + 1))
        done

        print_success "FreqUI 已启动 (PID: $pid)"

    else
        # 前台模式
        print_info "前台模式启动..."
        print_info "按 Ctrl+C 停止服务"
        echo ""

        # 如果需要打开浏览器，在后台启动 FreqUI 之前先打开
        if [ "$OPEN_BROWSER" = true ]; then
            print_info "步骤 5/5: 打开浏览器..."
            ( sleep 5 && open_browser ) &
        fi

        # 前台运行 npm
        npm run dev
        exit 0
    fi

    # 步骤 5: 打开浏览器（仅后台模式）
    if [ "$OPEN_BROWSER" = true ]; then
        print_info "步骤 5/5: 打开浏览器..."
        open_browser
    else
        print_info "步骤 5/5: 跳过打开浏览器"
    fi

    # 显示启动信息
    echo ""
    print_separator
    print_success "FreqUI 已启动！"
    echo ""
    echo "  📱 FreqUI 界面:  $FREQUI_URL"
    echo "  🤖 Bot API:      $BOT_API_URL"
    echo ""
    echo "  🔐 登录信息 (在 FreqUI 中使用):"
    echo "    - Bot 名称:  实盘Bot (任意)"
    echo "    - API 地址:  $BOT_API_URL"
    echo "    - 用户名:    freqtrade_user"
    echo "    - 密码:      freqtrade_pass123"
    echo ""
    echo "  📊 查看日志:     tail -f $LOG_FILE"
    echo "  🛑 停止服务:     $0 --stop"
    print_separator
    echo ""
}

################################################################################
# 打开浏览器
################################################################################

open_browser() {
    # 检测是否在 WSL 环境
    if command -v cmd.exe > /dev/null 2>&1; then
        print_info "正在打开浏览器..."
        cmd.exe /c start "$FREQUI_URL" 2>/dev/null
        print_success "浏览器已打开"
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$FREQUI_URL" 2>/dev/null
        print_success "浏览器已打开"
    elif command -v open > /dev/null 2>&1; then
        open "$FREQUI_URL" 2>/dev/null
        print_success "浏览器已打开"
    else
        print_info "请手动在浏览器中打开: $FREQUI_URL"
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
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        --no-browser)
            OPEN_BROWSER=false
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
        stop_ui
        ;;
    start)
        start_ui
        ;;
esac
