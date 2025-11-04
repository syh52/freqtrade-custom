#!/bin/bash

# Freqtrade Dry Run 启动脚本
# 此脚本会启动 Dry Run 模式并集成 Web UI

echo "════════════════════════════════════════════════════════════"
echo "  Freqtrade Dry Run 启动脚本"
echo "════════════════════════════════════════════════════════════"
echo ""

# 检查是否已有进程在运行
if pgrep -f "freqtrade trade" > /dev/null; then
    echo "⚠️  警告：检测到 Freqtrade 进程已在运行"
    echo ""
    read -p "是否要停止现有进程并重新启动？(y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] 停止现有进程..."
        pkill -f "freqtrade trade"
        sleep 3
    else
        echo "[INFO] 取消启动"
        exit 0
    fi
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 错误：未找到虚拟环境 (.venv)"
    echo "请先运行: python -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

# 检查配置文件
if [ ! -f "user_data/config.json" ]; then
    echo "❌ 错误：未找到配置文件 user_data/config.json"
    exit 1
fi

# 检查 dry_run 设置
if ! grep -q '"dry_run".*true' user_data/config-custom.json 2>/dev/null; then
    echo "⚠️  警告：请确保 config-custom.json 中 dry_run 设置为 true"
fi

echo "[INFO] 激活虚拟环境..."
source .venv/bin/activate

echo "[INFO] 启动 Freqtrade Dry Run 模式..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  配置信息："
echo "  - 模式: Dry Run (模拟交易)"
echo "  - 策略: $(grep -oP '(?<="strategy": ")[^"]*' user_data/config.json)"
echo "  - API 地址: http://127.0.0.1:8080"
echo "  - 日志文件: user_data/logs/freqtrade.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 后台启动
nohup freqtrade trade --config user_data/config.json > /dev/null 2>&1 &

# 获取进程 ID
FREQTRADE_PID=$!
echo "[SUCCESS] Freqtrade 已在后台启动 (PID: $FREQTRADE_PID)"
echo ""

# 等待服务启动
echo "[INFO] 等待服务启动..."
sleep 5

# 检查进程是否还在运行
if ps -p $FREQTRADE_PID > /dev/null; then
    echo "✅ Freqtrade 正在运行中！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  访问信息："
    echo "  🌐 Web UI: http://127.0.0.1:8080"
    echo "  👤 用户名: freqtrade_user"
    echo "  🔑 密码: freqtrade_pass123"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 实时监控命令："
    echo "  tail -f user_data/logs/freqtrade.log"
    echo ""
    echo "🛑 停止服务："
    echo "  ./stop_dryrun.sh"
    echo "  或: pkill -f 'freqtrade trade'"
    echo ""
else
    echo "❌ 启动失败，请检查日志："
    echo "  tail -50 user_data/logs/freqtrade.log"
    exit 1
fi
