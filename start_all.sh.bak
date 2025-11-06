#!/bin/bash

################################################################################
# Freqtrade 实盘交易 + Web UI 一键启动脚本
#
# 功能：
# - 自动启动实盘交易bot（14倍杠杆）
# - 自动启动FreqUI Web界面
# - 自动打开浏览器
################################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
FREQTRADE_DIR="/home/dministrator/Newproject/freqtrade"
FREQUI_DIR="/home/dministrator/Newproject/frequi"
FREQUI_URL="http://127.0.0.1:3000"
BOT_API_URL="http://127.0.0.1:8082"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Freqtrade 实盘交易 + Web UI 一键启动"
echo "════════════════════════════════════════════════════════════"
echo ""

cd "$FREQTRADE_DIR"

# 步骤1：停止旧进程
echo -e "${BLUE}[1/4]${NC} 清理旧进程..."

# 停止所有freqtrade交易进程
pkill -9 -f "freqtrade trade" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 已停止旧的交易bot"

# 停止FreqUI进程（彻底清理所有相关进程）
pkill -9 -f "vite" 2>/dev/null
pkill -9 -f "frequi" 2>/dev/null
pkill -9 -f "npm.*dev" 2>/dev/null
echo -e "  ${GREEN}✓${NC} 已停止旧的FreqUI"

# 清理3000-3010端口占用
for port in {3000..3010}; do
    PORT_PID=$(lsof -t -i:$port 2>/dev/null)
    if [ -n "$PORT_PID" ]; then
        kill -9 $PORT_PID 2>/dev/null
        echo -e "  ${YELLOW}!${NC} 清理端口 $port"
    fi
done

# 等待3000端口完全释放
echo -n "  等待3000端口释放"
for i in {1..15}; do
    if ! lsof -i:3000 >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":3000"; then
        echo ""
        break
    fi
    echo -n "."
    sleep 1
done

# 确保8082端口释放
PORT_PID=$(lsof -t -i:8082 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    kill -9 $PORT_PID 2>/dev/null
    echo -e "  ${GREEN}✓${NC} 已释放8082端口"
fi

# 等待端口完全释放（检查直到端口真正可用）
echo -n "  等待端口释放"
for i in {1..10}; do
    if ! lsof -i:8082 >/dev/null 2>&1 && ! ss -tlnp 2>/dev/null | grep -q ":8082"; then
        echo ""
        break
    fi
    echo -n "."
    sleep 1
done
echo -e "  ${GREEN}✓${NC} 清理完成"

# 步骤2：启动实盘交易bot
echo ""
echo -e "${BLUE}[2/4]${NC} 启动实盘交易bot..."
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
source .venv/bin/activate
nohup freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    >> user_data/logs/freqtrade.log 2>&1 &
BOT_PID=$!

sleep 5

# 检查bot是否启动成功
if ! ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "  ${RED}✗${NC} 交易bot启动失败！查看日志:"
    tail -20 user_data/logs/freqtrade.log
    exit 1
fi
echo -e "  ${GREEN}✓${NC} 交易bot已启动 (PID: $BOT_PID)"

# 步骤3：启动FreqUI
echo ""
echo -e "${BLUE}[3/4]${NC} 启动FreqUI Web界面..."
cd "$FREQUI_DIR"
nohup npm run dev > /tmp/frequi.log 2>&1 &
FREQUI_PID=$!

sleep 8

# 检查FreqUI是否启动成功
if ! ps -p $FREQUI_PID > /dev/null 2>&1; then
    echo -e "  ${RED}✗${NC} FreqUI启动失败！查看日志:"
    tail -20 /tmp/frequi.log
    exit 1
fi
echo -e "  ${GREEN}✓${NC} FreqUI已启动 (PID: $FREQUI_PID)"

# 步骤4：打开浏览器
echo ""
echo -e "${BLUE}[4/4]${NC} 打开浏览器..."
# 直接从WSL启动Windows浏览器，避免被Clash代理拦截
if command -v cmd.exe > /dev/null 2>&1; then
    cmd.exe /c start "$FREQUI_URL" 2>/dev/null
    echo -e "  ${GREEN}✓${NC} 浏览器已打开"
else
    echo -e "  ${YELLOW}!${NC} 请手动打开浏览器访问: $FREQUI_URL"
fi

# 显示最终状态
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}[SUCCESS]${NC} 所有服务已启动！"
echo ""
echo "  🤖 实盘Bot:     运行中 (PID: $BOT_PID)"
echo "  📱 FreqUI:      $FREQUI_URL"
echo "  🔗 Bot API:     $BOT_API_URL"
echo ""
echo "  💰 交易配置:"
echo "    - 策略:      NostalgiaForInfinityX7"
echo "    - 杠杆:      14倍"
echo "    - 交易对:    56个"
echo "    - 最大持仓:  12个 (9多+3空)"
echo ""
echo "  🔐 登录信息 (在FreqUI中使用):"
echo "    - API地址:   $BOT_API_URL"
echo "    - 用户名:    freqtrade_user"
echo "    - 密码:      freqtrade_pass123"
echo ""
echo "  📊 查看状态:"
echo "    - Bot日志:   tail -f $FREQTRADE_DIR/user_data/logs/freqtrade.log"
echo "    - UI日志:    tail -f /tmp/frequi.log"
echo ""
echo "  🛑 停止服务:"
echo "    - 停止Bot:   kill $BOT_PID"
echo "    - 停止UI:    kill $FREQUI_PID"
echo "    - 全部停止:  pkill -f 'freqtrade trade' && pkill -f 'vite.*frequi'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}提示:${NC} 浏览器打开后，点击右上角设置添加Bot连接"
echo ""
