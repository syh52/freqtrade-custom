#!/bin/bash

################################################################################
# FreqUI 一键启动脚本
#
# 功能：
# - 自动检查并停止旧进程
# - 启动FreqUI Web界面
# - 自动打开浏览器
################################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
FREQUI_DIR="/home/dministrator/Newproject/frequi"
FREQUI_URL="http://127.0.0.1:3000"
BOT_API_URL="http://127.0.0.1:8082"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  FreqUI 一键启动脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查FreqUI目录是否存在
if [ ! -d "$FREQUI_DIR" ]; then
    echo -e "${RED}[ERROR]${NC} FreqUI目录不存在: $FREQUI_DIR"
    exit 1
fi

# 停止旧的FreqUI进程
echo -e "${BLUE}[INFO]${NC} 检查并清理旧进程..."
pkill -f "vite.*frequi" 2>/dev/null && echo -e "${GREEN}[SUCCESS]${NC} 已停止旧的FreqUI进程"

# 检查node_modules是否存在
if [ ! -d "$FREQUI_DIR/node_modules" ]; then
    echo -e "${YELLOW}[WARNING]${NC} 依赖未安装，正在安装..."
    cd "$FREQUI_DIR" && npm install
fi

# 启动FreqUI
echo -e "${BLUE}[INFO]${NC} 启动FreqUI..."
cd "$FREQUI_DIR"
nohup npm run dev > /tmp/frequi.log 2>&1 &
FREQUI_PID=$!

# 等待启动
echo -e "${BLUE}[INFO]${NC} 等待FreqUI启动..."
sleep 5

# 检查进程是否还在运行
if ! ps -p $FREQUI_PID > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} FreqUI启动失败，查看日志:"
    tail -20 /tmp/frequi.log
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}[SUCCESS]${NC} FreqUI已启动！"
echo ""
echo "  📱 FreqUI界面: $FREQUI_URL"
echo "  🤖 Bot API:    $BOT_API_URL"
echo ""
echo "  登录信息："
echo "    用户名: freqtrade_user"
echo "    密码:   freqtrade_pass123"
echo ""
echo "  查看日志: tail -f /tmp/frequi.log"
echo "  停止服务: pkill -f 'vite.*frequi'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 尝试自动打开浏览器（使用WSL直接启动Windows浏览器，避免代理拦截）
if command -v cmd.exe > /dev/null 2>&1; then
    echo -e "${BLUE}[INFO]${NC} 正在打开浏览器..."
    cmd.exe /c start "$FREQUI_URL" 2>/dev/null
else
    echo -e "${YELLOW}[INFO]${NC} 请手动在浏览器中打开: $FREQUI_URL"
fi

echo ""
echo -e "${YELLOW}提示:${NC} 浏览器打开后，使用以下信息连接Bot："
echo ""
echo "  Bot名称: 实盘Bot (任意)"
echo "  API地址: $BOT_API_URL"
echo "  用户名: freqtrade_user"
echo "  密码: freqtrade_pass123"
echo ""
echo "按 Ctrl+C 退出此脚本（FreqUI将继续在后台运行）"
echo ""

# 持续显示日志（可选）
sleep 2
tail -f /tmp/frequi.log
