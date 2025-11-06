@echo off
REM Windows批处理文件 - 在WSL中启动Freqtrade实盘+Web UI
REM 双击此文件即可启动

echo.
echo ====================================================
echo   启动Freqtrade实盘交易 + Web UI
echo ====================================================
echo.

REM 在WSL中执行启动脚本
wsl -d Ubuntu -e bash -c "cd /home/dministrator/Newproject/freqtrade && ./start_all.sh"

pause
