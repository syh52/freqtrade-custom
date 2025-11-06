# PowerShell脚本 - 在WSL中启动Freqtrade实盘+Web UI
# 右键 -> "使用PowerShell运行"

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  启动Freqtrade实盘交易 + Web UI" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# 在WSL中执行启动脚本
wsl -d Ubuntu bash -c "cd /home/dministrator/Newproject/freqtrade && ./start_all.sh"

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
