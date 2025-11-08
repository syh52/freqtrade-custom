#!/bin/bash

################################################################################
# Backtest Analyzer 启动脚本
#
# 功能：
# - 一键启动 Streamlit 分析界面
# - 自动清理旧进程和缓存
# - 支持前台/后台运行
# - 自动激活虚拟环境
################################################################################

# 配置
PROJECT_DIR="/home/dministrator/Newproject/freqtrade"
VENV_PATH="$PROJECT_DIR/.venv"
APP_PATH="$PROJECT_DIR/backtest_analyzer/app/main.py"
STREAMLIT_PORT=8501
LOG_FILE="/tmp/backtest_analyzer.log"
DAEMON_MODE=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# 辅助函数
################################################################################

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

print_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC}  $1"
}

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

show_help() {
    cat << EOF
Backtest Analyzer 启动脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -d, --daemon            后台运行模式
    --stop                  停止运行中的分析器

示例:
    $0                      # 前台运行（默认）
    $0 -d                   # 后台运行
    $0 --stop               # 停止分析器

EOF
    exit 0
}

################################################################################
# 停止 Streamlit
################################################################################

stop_analyzer() {
    print_header "停止 Backtest Analyzer"

    local pids
    pids=$(pgrep -f "streamlit run.*backtest_analyzer")

    if [ -z "$pids" ]; then
        print_info "Backtest Analyzer 未运行"
        exit 0
    fi

    print_info "找到以下进程："
    ps aux | grep -E "streamlit.*backtest_analyzer" | grep -v grep || true
    echo ""

    for pid in $pids; do
        print_info "正在停止进程 $pid..."
        kill -TERM "$pid" 2>/dev/null

        # 等待进程结束
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 0.5
            count=$((count + 1))
        done

        # 如果还没结束，强制 kill
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "进程 $pid 未响应，强制停止..."
            kill -KILL "$pid" 2>/dev/null
        fi
    done

    print_success "Backtest Analyzer 已停止"
    exit 0
}

################################################################################
# 启动 Analyzer
################################################################################

start_analyzer() {
    print_header "Backtest Analyzer 启动脚本"

    # 步骤 1: 切换到项目目录
    print_info "步骤 1/6: 切换到项目目录..."
    cd "$PROJECT_DIR" || {
        print_error "无法进入项目目录: $PROJECT_DIR"
        exit 1
    }
    print_success "当前目录: $(pwd)"

    # 步骤 2: 检查虚拟环境
    print_info "步骤 2/6: 检查虚拟环境..."
    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        exit 1
    fi
    print_success "虚拟环境存在"

    # 步骤 3: 检查应用文件
    print_info "步骤 3/6: 检查应用文件..."
    if [ ! -f "$APP_PATH" ]; then
        print_error "应用文件不存在: $APP_PATH"
        exit 1
    fi
    print_success "应用文件存在"

    # 步骤 4: 停止旧进程
    print_info "步骤 4/6: 清理旧进程..."
    local old_pids
    old_pids=$(pgrep -f "streamlit run.*backtest_analyzer" || true)

    if [ -n "$old_pids" ]; then
        print_warning "发现旧进程，正在停止..."
        for pid in $old_pids; do
            kill -TERM "$pid" 2>/dev/null || true
        done
        sleep 2

        # 强制 kill 未结束的进程
        for pid in $old_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
        print_success "旧进程已清理"
    else
        print_success "无旧进程需要清理"
    fi

    # 步骤 5: 清理缓存
    print_info "步骤 5/6: 清理 Streamlit 缓存..."
    rm -rf ~/.streamlit/cache 2>/dev/null || true
    print_success "缓存已清理"

    # 步骤 6: 启动应用
    print_info "步骤 6/6: 启动 Streamlit 应用..."

    # 激活虚拟环境并启动
    if [ "$DAEMON_MODE" = true ]; then
        # 后台模式
        print_info "后台模式启动..."
        source "$VENV_PATH/bin/activate"
        nohup streamlit run "$APP_PATH" --server.port $STREAMLIT_PORT > "$LOG_FILE" 2>&1 &
        local pid=$!
        sleep 3

        # 检查进程是否还在运行
        if ! kill -0 "$pid" 2>/dev/null; then
            print_error "启动失败，查看日志: $LOG_FILE"
            tail -20 "$LOG_FILE"
            exit 1
        fi

        print_success "Backtest Analyzer 已启动 (PID: $pid)"

        # 显示访问信息
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_success "启动成功！"
        echo ""
        echo "  🌐 访问地址:     http://127.0.0.1:$STREAMLIT_PORT"
        echo "  📊 查看日志:     tail -f $LOG_FILE"
        echo "  🛑 停止服务:     $0 --stop"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

    else
        # 前台模式
        print_info "前台模式启动..."
        print_info "按 Ctrl+C 停止服务"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_success "正在启动..."
        echo ""
        echo "  🌐 访问地址:     http://127.0.0.1:$STREAMLIT_PORT"
        echo "  🛑 停止服务:     按 Ctrl+C 或运行 $0 --stop"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        source "$VENV_PATH/bin/activate"
        streamlit run "$APP_PATH" --server.port $STREAMLIT_PORT
        exit 0
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
        stop_analyzer
        ;;
    start)
        start_analyzer
        ;;
esac
