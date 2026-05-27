# 停掉 Scheduled Task
Unregister-ScheduledTask -TaskName "OpenClaw Gateway" -Confirm:$false -ErrorAction SilentlyContinue

# 杀掉所有监听 18789 的残留进程
$pids = (Get-NetTCPConnection -LocalPort 18789 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($pid in $pids) {
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "已清理残留进程 PID $pid"
}

# 以无窗口后台进程启动 Gateway
Start-Process -FilePath "C:\Program Files\nodejs\node.exe" `
  -ArgumentList "D:\npm-global\node_modules\openclaw\dist\index.js","gateway","--port","18789" `
  -WindowStyle Hidden `
  -WorkingDirectory "D:\OpenClaw"

Write-Host "Gateway 已后台启动（无窗口模式）"
