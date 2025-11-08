#!/bin/bash
# Pairlist检查脚本 - 查看实盘选中的币种

echo "================================================================"
echo "实盘币种挑选检查"
echo "================================================================"
echo ""

# 检查Bot是否运行
BOT_RUNNING=$(ps aux | grep "freqtrade trade" | grep -v grep | wc -l)

if [ "$BOT_RUNNING" -eq 0 ]; then
    echo "❌ 机器人未运行"
    echo ""
    echo "建议: 启动机器人后再运行此脚本"
    echo "启动命令: ./ft start --bot -d"
    exit 1
fi

echo "✅ 机器人正在运行"
echo ""

# 方法1: 从API获取whitelist (最准确)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "方法1: 从Bot API获取实时whitelist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

WHITELIST=$(curl -s http://127.0.0.1:8082/api/v1/whitelist \
  -u freqtrade_user:freqtrade_pass123 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$WHITELIST" ]; then
    COUNT=$(echo "$WHITELIST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['whitelist']))" 2>/dev/null)

    if [ ! -z "$COUNT" ]; then
        echo "📊 当前选中币种数量: $COUNT 个"
        echo ""
        echo "币种列表:"
        echo "$WHITELIST" | python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join(['  ' + str(i+1) + '. ' + p for i, p in enumerate(data['whitelist'])]))" 2>/dev/null
    else
        echo "⚠️  无法解析API返回数据"
    fi
else
    echo "❌ 无法连接到Bot API (端口8082)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "方法2: 从日志文件获取"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -f "user_data/logs/freqtrade.log" ]; then
        echo "查找最近的pairlist日志..."
        grep -i "whitelist" user_data/logs/freqtrade.log | tail -10
    else
        echo "❌ 日志文件不存在: user_data/logs/freqtrade.log"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "验证黑名单生效 (检查这些币种是否被排除)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查刚加入黑名单的5个垃圾币是否被正确排除
BLACKLISTED_COINS=("HOOK/USDT:USDT" "MINA/USDT:USDT" "KAIA/USDT:USDT" "BAND/USDT:USDT" "HIGH/USDT:USDT")

if [ ! -z "$WHITELIST" ]; then
    echo "检查新加入黑名单的5个垃圾币:"
    for coin in "${BLACKLISTED_COINS[@]}"; do
        if echo "$WHITELIST" | grep -q "$coin"; then
            echo "  ❌ $coin - 仍在whitelist中 (黑名单未生效!)"
        else
            echo "  ✅ $coin - 已被正确排除"
        fi
    done
else
    echo "⚠️  无法验证 (API不可用)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "当前持仓检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OPEN_TRADES=$(curl -s http://127.0.0.1:8082/api/v1/status \
  -u freqtrade_user:freqtrade_pass123 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$OPEN_TRADES" ]; then
    TRADE_COUNT=$(echo "$OPEN_TRADES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null)

    if [ "$TRADE_COUNT" = "0" ]; then
        echo "📊 当前无持仓"
    else
        echo "📊 当前持仓: $TRADE_COUNT 个"
        echo "$OPEN_TRADES" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  - {t['pair']} (收益: {t['profit_pct']:.2f}%)\") for t in data]" 2>/dev/null
    fi
else
    echo "⚠️  无法获取持仓信息"
fi

echo ""
echo "================================================================"
echo "提示:"
echo "  - 币种列表每30分钟刷新一次 (根据pairlist配置)"
echo "  - 如果发现问题,请检查 user_data/logs/freqtrade.log"
echo "  - FreqUI访问: http://localhost:3000"
echo "================================================================"
