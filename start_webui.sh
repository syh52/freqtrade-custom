#!/bin/bash

################################################################################
# Freqtrade Web UI 智能启动脚本
#
# 功能：
# - 自动检测并清理占用端口的旧进程
# - 激活虚拟环境
# - 启动 Web UI
# - 提供多种启动模式（前台/后台）
#
# 使用方法：
#   ./start_webui.sh          # 前台运行
#   ./start_webui.sh -d       # 后台运行（daemon 模式）
#   ./start_webui.sh -p 9090  # 指定端口
#   ./start_webui.sh --help   # 查看帮助
################################################################################

# 不使用 set -e 和 set -u，避免意外退出
# set -o pipefail 也可能导致问题，暂时禁用

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/user_data/config.json"
VENV_PATH="${SCRIPT_DIR}/.venv"
DEFAULT_PORT=8080
PORT=$DEFAULT_PORT
DAEMON_MODE=false
LOG_FILE="${SCRIPT_DIR}/webui.log"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Freqtrade Web UI 智能启动脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -p, --port PORT         指定端口（默认: 8080）
    -c, --config FILE       指定配置文件（默认: user_data/config.json）
    -d, --daemon            后台运行模式
    -s, --status            查看运行状态
    --stop                  停止所有 Freqtrade Web UI 进程
    --restart               重启服务

示例:
    $0                      # 前台运行在端口 8080（自动停止旧进程）
    $0 -d                   # 后台运行
    $0 -p 9090              # 使用端口 9090
    $0 -d -p 9090           # 后台运行在端口 9090
    $0 --stop               # 停止所有 Web UI 进程
    $0 --restart            # 重启服务

说明:
    - 脚本会自动停止监听指定端口的旧 freqtrade 进程
    - 只影响 freqtrade 进程，不会影响其他程序（如编辑器、浏览器等）
    - 如果端口被非 freqtrade 程序占用，请使用 -p 指定其他端口

EOF
    exit 0
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖项..."

    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        print_info "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -e ."
        exit 1
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "配置文件不存在: $CONFIG_FILE"
        print_info "请先运行: freqtrade new-config --config $CONFIG_FILE"
        exit 1
    fi

    print_success "依赖检查通过"
}

# 检查端口占用（只检查 LISTEN 状态）
check_port_usage() {
    local port=$1
    print_info "检查端口 $port 占用情况..."

    # 使用 lsof 检查端口（只检查 LISTEN 状态）
    if command -v lsof > /dev/null 2>&1; then
        # -sTCP:LISTEN 只查找监听状态的进程
        local listen_count
        listen_count=$(lsof -i ":${port}" -sTCP:LISTEN 2>/dev/null | wc -l || echo "0")
        if [ "$listen_count" -gt 0 ]; then
            return 0  # 端口被占用（有进程在监听）
        fi
    else
        # 备用方案：使用 ss (更现代的替代品)
        if command -v ss > /dev/null 2>&1; then
            # ss -tuln 只显示监听状态的端口
            if ss -tuln 2>/dev/null | grep -q ":${port} "; then
                return 0  # 端口被占用
            fi
        elif command -v netstat > /dev/null 2>&1; then
            # netstat -tuln 只显示监听状态的端口
            if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
                return 0  # 端口被占用
            fi
        else
            print_warning "无法检查端口占用（缺少 lsof/ss/netstat 工具）"
            return 1
        fi
    fi

    return 1  # 端口未被占用
}

# 停止占用端口的进程（只停止 LISTEN 状态的 freqtrade 进程）
stop_port_process() {
    local port=$1

    print_warning "端口 $port 已被占用"

    # 只查找监听（LISTEN）该端口的 freqtrade 进程
    # 使用 lsof 并过滤 LISTEN 状态，且进程名包含 freqtrade
    local freqtrade_pids
    freqtrade_pids=$(lsof -i ":${port}" -sTCP:LISTEN 2>/dev/null | grep freqtrade | awk '{print $2}' | sort -u || true)

    if [ -z "$freqtrade_pids" ]; then
        print_warning "未找到监听端口 $port 的 freqtrade 进程"

        # 显示所有占用该端口的进程（仅供参考）
        print_info "当前占用端口的所有进程："
        lsof -i ":${port}" 2>/dev/null | head -n 20 || true

        echo ""
        print_info "如果端口被其他程序占用，请手动处理或使用其他端口："
        print_info "  ./start_webui.sh -p 9090"
        exit 1
    fi

    # 显示将要停止的 freqtrade 进程
    print_info "找到监听端口 $port 的 freqtrade 进程，正在自动停止..."
    for pid in $freqtrade_pids; do
        ps -p "$pid" -o pid,user,cmd 2>/dev/null || true
    done
    echo ""

    # 自动停止进程（不需要确认）
    for pid in $freqtrade_pids; do
        # 再次确认这是 freqtrade 进程
        if ps -p "$pid" -o cmd= 2>/dev/null | grep -q "freqtrade"; then
            print_info "停止进程 $pid"
            kill -TERM "$pid" 2>/dev/null || true

            # 等待进程退出（最多5秒）
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ "$count" -lt 50 ]; do
                sleep 0.1
                count=$((count + 1))
            done

            # 如果进程还在运行，强制杀死
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "进程 $pid 未响应，强制杀死"
                kill -9 "$pid" 2>/dev/null || true
            fi

            print_success "进程 $pid 已停止"
        else
            print_warning "跳过非 freqtrade 进程 $pid"
        fi
    done

    # 再次检查端口
    sleep 1
    if check_port_usage "$port"; then
        print_error "端口 $port 仍被占用，请手动检查"
        lsof -i ":${port}" 2>/dev/null | head -n 20 || true
        exit 1
    fi

    print_success "已清理端口 $port"
}

# 停止所有 Freqtrade webserver 进程
stop_all_webui() {
    print_info "停止所有 Freqtrade 进程（包含 Web UI）..."

    # 查找所有 freqtrade 进程（包括 webserver 和 trade 命令）
    local pids
    pids=$(pgrep -f "freqtrade (webserver|trade)" 2>/dev/null || true)

    if [ -z "$pids" ]; then
        print_info "没有运行中的 Freqtrade 进程"
        return 0
    fi

    print_info "找到以下进程:"
    ps aux | grep -E "freqtrade (webserver|trade)" | grep -v grep || true

    for pid in $pids; do
        print_info "停止进程 $pid"
        kill -TERM "$pid" 2>/dev/null || true
    done

    # 等待进程退出
    sleep 2

    # 检查是否还有进程
    pids=$(pgrep -f "freqtrade (webserver|trade)" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_warning "部分进程未响应，强制杀死"
        for pid in $pids; do
            kill -9 "$pid" 2>/dev/null || true
        done
    fi

    print_success "所有 Freqtrade 进程已停止"
}

# 查看运行状态
show_status() {
    print_info "Freqtrade 运行状态:"
    echo ""

    local pids
    pids=$(pgrep -f "freqtrade (webserver|trade)" 2>/dev/null || true)

    if [ -z "$pids" ]; then
        print_info "Freqtrade 未运行"
    else
        print_success "Freqtrade 正在运行"
        echo ""
        ps aux | head -n 1 || true
        ps aux | grep -E "freqtrade (webserver|trade)" | grep -v grep || true
        echo ""

        # 显示监听的端口
        print_info "监听的端口:"
        for pid in $pids; do
            lsof -Pan -p "$pid" -i 2>/dev/null | grep LISTEN || echo "  进程 $pid: 无法获取端口信息"
        done
    fi

    # 如果有日志文件，显示最后几行
    if [ -f "$LOG_FILE" ]; then
        echo ""
        print_info "最近日志 (最后 10 行):"
        tail -n 10 "$LOG_FILE" || true
    fi
}

# 启动 Web UI
start_webui() {
    print_info "启动 Freqtrade Web UI..."

    # 直接使用虚拟环境中的 freqtrade 可执行文件（不使用 source）
    local FREQTRADE_BIN="${VENV_PATH}/bin/freqtrade"

    print_info "使用虚拟环境: $VENV_PATH"

    # 检查 freqtrade 命令是否可用
    if [ ! -f "$FREQTRADE_BIN" ]; then
        print_error "freqtrade 命令不存在: $FREQTRADE_BIN"
        print_info "请确保已正确安装 freqtrade: pip install -e ."
        exit 1
    fi

    if [ ! -x "$FREQTRADE_BIN" ]; then
        print_error "freqtrade 命令不可执行: $FREQTRADE_BIN"
        exit 1
    fi

    # 构建启动命令（使用数组避免引号问题）
    local cmd_array=("$FREQTRADE_BIN" "webserver" "--config" "$CONFIG_FILE")

    if [ "$PORT" -ne "$DEFAULT_PORT" ]; then
        cmd_array+=("--listen-port" "$PORT")
    fi

    print_info "启动命令: ${cmd_array[*]}"
    print_info "配置文件: $CONFIG_FILE"
    print_info "监听端口: $PORT"

    # 启动服务
    if [ "$DAEMON_MODE" = true ]; then
        print_info "后台模式启动..."
        nohup "${cmd_array[@]}" > "$LOG_FILE" 2>&1 &
        local pid=$!
        sleep 2

        # 检查进程是否还在运行
        if kill -0 "$pid" 2>/dev/null; then
            print_success "Web UI 已在后台启动 (PID: $pid)"
            print_info "日志文件: $LOG_FILE"
            print_info "查看日志: tail -f $LOG_FILE"
            print_info "访问地址: http://127.0.0.1:$PORT"
            print_info "停止服务: $0 --stop"
        else
            print_error "启动失败，请查看日志: $LOG_FILE"
            tail -n 20 "$LOG_FILE"
            exit 1
        fi
    else
        print_info "前台模式启动..."
        print_success "Web UI 正在启动..."
        print_info "访问地址: http://127.0.0.1:$PORT"
        print_info "按 Ctrl+C 停止服务"
        echo ""
        exec "${cmd_array[@]}"
    fi
}

# 重启服务
restart_webui() {
    print_info "重启 Freqtrade Web UI..."
    stop_all_webui
    sleep 2
    start_webui
}

# 解析命令行参数
ACTION="start"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -s|--status)
            ACTION="status"
            shift
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --restart)
            ACTION="restart"
            shift
            ;;
        *)
            print_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 打印欢迎信息
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Freqtrade Web UI 智能启动脚本"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 执行操作
case $ACTION in
    status)
        show_status
        ;;
    stop)
        stop_all_webui
        ;;
    restart)
        restart_webui
        ;;
    start)
        check_dependencies

        # 检查端口占用，如果被占用则自动停止
        if check_port_usage $PORT; then
            stop_port_process $PORT
        else
            print_success "端口 $PORT 可用"
        fi

        start_webui
        ;;
esac

echo ""
