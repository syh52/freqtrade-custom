#!/bin/bash

# Freqtrade Web UI 启动脚本（回测模式）
# 此脚本使用回测配置启动 Web UI，支持 Web UI 中的回测功能

echo "════════════════════════════════════════════════════════════"
echo "  Freqtrade Web UI 启动脚本（回测模式）"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查端口
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告：端口 8080 已被占用"
    echo "请先停止现有服务："
    echo "  pkill -f 'freqtrade webserver'"
    exit 1
fi

# 检查配置文件
if [ ! -f "user_data/config-backtest.json" ]; then
    echo "❌ 错误：未找到回测配置文件 user_data/config-backtest.json"
    exit 1
fi

echo "[INFO] 激活虚拟环境..."
source .venv/bin/activate

echo "[INFO] 启动 Web UI（回测模式）..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  配置信息："
echo "  - 模式: 回测模式（Web UI）"
echo "  - 配置: config-backtest.json"
echo "  - 交易对: 34个静态列表"
echo "  - API 地址: http://127.0.0.1:8080"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "[SUCCESS] Web UI 正在启动..."
echo "[INFO] 访问地址: http://127.0.0.1:8080"
echo "[INFO] 按 Ctrl+C 停止服务"
echo ""

freqtrade webserver --config user_data/config-backtest.json
