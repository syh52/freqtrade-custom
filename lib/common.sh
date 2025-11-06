#!/bin/bash

################################################################################
# Freqtrade 共享函数库
#
# 提供通用的工具函数，供其他脚本复用
################################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${SCRIPT_DIR}/.venv"
FREQUI_DIR="/home/dministrator/Newproject/frequi"

# 默认端口
BOT_PORT=8082
UI_PORT=3000

################################################################################
# 打印函数
################################################################################

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

################################################################################
# 端口管理函数
################################################################################

# 检查端口是否被占用（只检查 LISTEN 状态）
# 参数: $1 - 端口号
# 返回: 0 表示端口被占用，1 表示端口可用
check_port() {
    local port=$1

    if command -v lsof > /dev/null 2>&1; then
        # -sTCP:LISTEN 只查找监听状态的进程
        local listen_count
        listen_count=$(lsof -i ":${port}" -sTCP:LISTEN 2>/dev/null | wc -l || echo "0")
        if [ "$listen_count" -gt 0 ]; then
            return 0  # 端口被占用
        fi
    elif command -v ss > /dev/null 2>&1; then
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

    return 1  # 端口未被占用
}

# 停止占用端口的进程
# 参数: $1 - 端口号
#       $2 - 进程名称模式（用于过滤，例如 "freqtrade" 或 "vite|npm"）
# 返回: 0 表示成功，1 表示失败
kill_port_process() {
    local port=$1
    local process_pattern=$2

    # 查找监听该端口的进程，并过滤指定模式
    local pids
    pids=$(lsof -i ":${port}" -sTCP:LISTEN 2>/dev/null | grep -E "$process_pattern" | awk '{print $2}' | sort -u || true)

    if [ -z "$pids" ]; then
        print_warning "未找到监听端口 $port 的 $process_pattern 进程"

        # 显示所有占用该端口的进程（仅供参考）
        print_info "当前占用端口的所有进程："
        lsof -i ":${port}" 2>/dev/null | head -n 20 || true
        return 1
    fi

    # 显示将要停止的进程
    print_info "找到监听端口 $port 的进程，正在停止..."
    for pid in $pids; do
        ps -p "$pid" -o pid,user,cmd 2>/dev/null || true
    done
    echo ""

    # 停止进程
    for pid in $pids; do
        # 再次确认进程匹配模式
        if ps -p "$pid" -o cmd= 2>/dev/null | grep -qE "$process_pattern"; then
            stop_process_gracefully "$pid"
        fi
    done

    return 0
}

# 等待端口释放
# 参数: $1 - 端口号
#       $2 - 超时时间（秒，默认 10 秒）
# 返回: 0 表示端口已释放，1 表示超时
wait_port_ready() {
    local port=$1
    local timeout=${2:-10}
    local count=0

    print_info "等待端口 $port 释放..."

    while [ $count -lt $timeout ]; do
        if ! check_port "$port"; then
            print_success "端口 $port 已释放"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    print_error "端口 $port 释放超时（${timeout}秒）"
    return 1
}

################################################################################
# 进程管理函数
################################################################################

# 查找 Freqtrade Bot 进程
# 返回: 进程 ID 列表（可能为空）
find_bot_process() {
    pgrep -f "freqtrade trade" 2>/dev/null || true
}

# 查找 FreqUI 进程
# 返回: 进程 ID 列表（可能为空）
find_ui_process() {
    pgrep -f "vite.*frequi\|npm.*dev.*frequi" 2>/dev/null || true
}

# 优雅停止进程
# 参数: $1 - 进程 ID
# 返回: 0 表示成功，1 表示失败
stop_process_gracefully() {
    local pid=$1

    if ! kill -0 "$pid" 2>/dev/null; then
        print_warning "进程 $pid 不存在或已停止"
        return 0
    fi

    print_info "停止进程 $pid (优雅模式)"
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程退出（最多5秒）
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ "$count" -lt 50 ]; do
        sleep 0.1
        count=$((count + 1))
    done

    # 如果进程还在运行，强制杀死
    if kill -0 "$pid" 2>/dev/null; then
        print_warning "进程 $pid 未响应，强制停止"
        kill -KILL "$pid" 2>/dev/null || true
        sleep 0.5
    fi

    # 验证进程已停止
    if kill -0 "$pid" 2>/dev/null; then
        print_error "无法停止进程 $pid"
        return 1
    fi

    print_success "进程 $pid 已停止"
    return 0
}

################################################################################
# 健康检查函数
################################################################################

# 检查 Bot API 是否响应
# 返回: 0 表示健康，1 表示不健康
check_bot_health() {
    local url="http://127.0.0.1:${BOT_PORT}/api/v1/ping"

    if command -v curl > /dev/null 2>&1; then
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            return 0
        fi
    elif command -v wget > /dev/null 2>&1; then
        if wget -q --timeout=2 -O /dev/null "$url" 2>/dev/null; then
            return 0
        fi
    fi

    return 1
}

# 检查 FreqUI 是否响应
# 返回: 0 表示健康，1 表示不健康
check_ui_health() {
    local url="http://127.0.0.1:${UI_PORT}"

    if command -v curl > /dev/null 2>&1; then
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            return 0
        fi
    elif command -v wget > /dev/null 2>&1; then
        if wget -q --timeout=2 -O /dev/null "$url" 2>/dev/null; then
            return 0
        fi
    fi

    return 1
}

################################################################################
# 依赖检查函数
################################################################################

# 检查虚拟环境是否存在
# 返回: 0 表示存在，1 表示不存在
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        print_info "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -e ."
        return 1
    fi
    return 0
}

# 检查 Freqtrade 命令是否可用
# 返回: 0 表示可用，1 表示不可用
check_freqtrade_command() {
    local freqtrade_bin="${VENV_PATH}/bin/freqtrade"

    if [ ! -f "$freqtrade_bin" ]; then
        print_error "Freqtrade 命令不存在: $freqtrade_bin"
        print_info "请确保已正确安装: pip install -e ."
        return 1
    fi

    if [ ! -x "$freqtrade_bin" ]; then
        print_error "Freqtrade 命令不可执行: $freqtrade_bin"
        return 1
    fi

    return 0
}

# 检查 FreqUI 目录是否存在
# 返回: 0 表示存在，1 表示不存在
check_frequi_dir() {
    if [ ! -d "$FREQUI_DIR" ]; then
        print_error "FreqUI 目录不存在: $FREQUI_DIR"
        return 1
    fi
    return 0
}

# 检查配置文件是否存在
# 参数: $1 - 配置文件路径
# 返回: 0 表示存在，1 表示不存在
check_config_file() {
    local config_file=$1

    if [ ! -f "$config_file" ]; then
        print_error "配置文件不存在: $config_file"
        return 1
    fi

    return 0
}

################################################################################
# 工具函数
################################################################################

# 打印分隔线
print_separator() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 打印标题
print_header() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
    echo ""
}
