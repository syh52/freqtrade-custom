#!/bin/bash

# Freqtrade Dry Run 停止脚本

echo "════════════════════════════════════════════════════════════"
echo "  Freqtrade Dry Run 停止脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 查找正在运行的 freqtrade 进程
PIDS=$(pgrep -f "freqtrade trade")

if [ -z "$PIDS" ]; then
    echo "ℹ️  未找到正在运行的 Freqtrade 进程"
    exit 0
fi

echo "[INFO] 发现以下 Freqtrade 进程："
ps aux | grep "freqtrade trade" | grep -v grep

echo ""
echo "[INFO] 正在停止进程..."

# 优雅停止
pkill -TERM -f "freqtrade trade"
sleep 3

# 检查是否还有进程
REMAINING=$(pgrep -f "freqtrade trade")
if [ -z "$REMAINING" ]; then
    echo "✅ Freqtrade 已成功停止"
else
    echo "⚠️  进程未响应，强制终止..."
    pkill -KILL -f "freqtrade trade"
    sleep 1

    if pgrep -f "freqtrade trade" > /dev/null; then
        echo "❌ 无法停止进程，请手动检查"
        exit 1
    else
        echo "✅ Freqtrade 已强制停止"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  所有 Freqtrade 进程已停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
