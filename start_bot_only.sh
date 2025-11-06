#!/bin/bash
################################################################################
# 简化版实盘Bot启动脚本（不包含FreqUI）
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "════════════════════════════════════════"
echo "  Freqtrade 实盘Bot启动"
echo "════════════════════════════════════════"
echo ""

cd /home/dministrator/Newproject/freqtrade

# 停止旧进程
echo -e "${BLUE}[1/2]${NC} 清理旧进程..."
pkill -9 -f "freqtrade trade" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 已停止旧bot"
sleep 3

# 启动bot
echo ""
echo -e "${BLUE}[2/2]${NC} 启动实盘bot..."
source .venv/bin/activate
export https_proxy=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897

nohup freqtrade trade \
    --config user_data/config-custom.json \
    --config user_data/config-private.json \
    --strategy NostalgiaForInfinityX7 \
    >> user_data/logs/freqtrade.log 2>&1 &

BOT_PID=$!
sleep 5

# 检查启动状态
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Bot已启动 (PID: $BOT_PID)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}[成功]${NC} 实盘Bot运行中！"
    echo ""
    echo "  🤖 Bot PID:    $BOT_PID"
    echo "  🔗 API地址:    http://127.0.0.1:8082"
    echo "  📊 查看日志:   tail -f user_data/logs/freqtrade.log"
    echo "  🛑 停止Bot:    kill $BOT_PID"
    echo ""
    echo "  💡 使用API查看状态："
    echo "     curl http://127.0.0.1:8082/api/v1/status | python3 -m json.tool"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo -e "  ${RED}✗${NC} Bot启动失败，查看日志:"
    tail -30 user_data/logs/freqtrade.log
    exit 1
fi

echo ""
