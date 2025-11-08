#!/bin/bash
# Check backtest status and progress

echo "================================================================"
echo "回测状态检查"
echo "================================================================"
echo ""

# Check if backtest is running
BACKTEST_PID=$(ps aux | grep "freqtrade backtesting" | grep -v grep | awk '{print $2}')

if [ -z "$BACKTEST_PID" ]; then
    echo "❌ 回测进程未运行"
    echo ""
    echo "检查最后的输出:"
    tail -50 backtest_output.log
else
    echo "✅ 回测进程正在运行 (PID: $BACKTEST_PID)"

    # Get CPU and memory usage
    CPU=$(ps aux | grep $BACKTEST_PID | grep -v grep | awk '{print $3}')
    MEM=$(ps aux | grep $BACKTEST_PID | grep -v grep | awk '{print $4}')
    echo "   CPU使用率: ${CPU}%"
    echo "   内存使用率: ${MEM}%"
    echo ""

    # Show recent log entries
    echo "最新日志 (最后20行):"
    echo "----------------------------------------------------------------"
    tail -20 backtest_output.log
    echo "----------------------------------------------------------------"
    echo ""

    # Count lines in log to estimate progress
    LOG_LINES=$(wc -l < backtest_output.log)
    echo "日志行数: $LOG_LINES"
fi

echo ""
echo "================================================================"
echo "提示:"
echo "  - 回测可能需要30分钟到2小时完成(75个币种,6个月数据)"
echo "  - 使用 'tail -f backtest_output.log' 实时查看进度"
echo "  - 使用 './check_backtest_status.sh' 随时检查状态"
echo "================================================================"
