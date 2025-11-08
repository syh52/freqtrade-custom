#!/bin/bash
# Whitelist生成监控脚本

echo "开始监控whitelist生成..."
echo "按 Ctrl+C 停止监控"
echo ""

LAST_LINE_COUNT=$(wc -l < user_data/logs/freqtrade.log)

while true; do
    # 检查是否有新的whitelist日志
    NEW_LINES=$(tail -n +$LAST_LINE_COUNT user_data/logs/freqtrade.log)

    if echo "$NEW_LINES" | grep -q "Whitelist with"; then
        echo ""
        echo "════════════════════════════════════════════════════════════"
        echo "✅ Whitelist已生成！"
        echo "════════════════════════════════════════════════════════════"
        echo ""

        # 提取并显示whitelist信息
        echo "$NEW_LINES" | grep "Whitelist with"

        echo ""
        echo "正在运行验证脚本..."
        echo ""

        # 运行验证脚本
        ./check_pairlist.sh

        break
    fi

    # 更新已读取的行数
    LAST_LINE_COUNT=$(wc -l < user_data/logs/freqtrade.log)

    # 每5秒检查一次
    sleep 5

    # 显示进度点
    echo -n "."
done

echo ""
echo "监控结束"
