<#
一键修复 .openclaw 符号链接 → 真实目录（提权版）
解决 OpenClaw exec 工具因 symlink 安全检查被完全阻塞的问题
#>

$ErrorActionPreference = "Stop"
$logFile = "$env:TEMP\fix-openclaw-log.txt"

function Log($msg) {
    $msg | Out-File -FilePath $logFile -Append
    Write-Host $msg
}

# 检查是否管理员，不是则自提权
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Log "[INFO] 非管理员权限，请求提权..."
    $script = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Log "============================================"
Log "  OpenClaw .openclaw 目录修复工具（提权版）"
Log "============================================"

$symlinkPath = "$env:USERPROFILE\.openclaw"
$backupPath  = "$env:USERPROFILE\.openclaw.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"

try {
    # 检测符号链接
    $item = Get-Item $symlinkPath -Force -ErrorAction Stop
    $isLink = $item.LinkType -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    
    if (-not $isLink) {
        Log "[OK] 不是符号链接，无需修复"
        Read-Host "按回车退出"
        exit 0
    }
    
    # 获取链接信息
    $linkType = if ($item.LinkType) { $item.LinkType } else { "ReparsePoint/Junction" }
    $target = if ($item.Target) { $item.Target } else { "（未知目标）" }
    Log "[INFO] 检测到链接: $linkType -> $target"
    
    # 备份
    Log "[STEP 1/3] 备份到: $backupPath"
    robocopy $symlinkPath $backupPath /E /COPY:DAT /R:2 /W:2 /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "备份失败 (robocopy exit code: $LASTEXITCODE)" }
    Log "[OK] 备份完成"
    
    # 删链接
    Log "[STEP 2/3] 删除链接..."
    # 先尝试正常删除
    Remove-Item -Path $symlinkPath -Force -ErrorAction SilentlyContinue
    if (Test-Path $symlinkPath) {
        # 如果还在，用 cmd 删
        cmd /c "rmdir `"$symlinkPath`"" 2>&1 | Out-Null
    }
    if (Test-Path $symlinkPath) {
        throw "无法删除符号链接"
    }
    Log "[OK] 链接已删除"
    
    # 重建真实目录
    Log "[STEP 3/3] 重建真实目录..."
    New-Item -Path $symlinkPath -ItemType Directory -Force | Out-Null
    robocopy $backupPath $symlinkPath /E /COPY:DAT /R:2 /W:2 /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "恢复数据失败" }
    Log "[OK] 目录重建完成，数据已恢复"
    
    Log ""
    Log "============================================"
    Log "  修复成功！请重启 OpenClaw Gateway"
    Log "============================================"
    
} catch {
    Log "[ERROR] $($_.Exception.Message)"
    Log "[ERROR] 修复失败，备份在: $backupPath"
    Read-Host "按回车退出"
    exit 1
}

Read-Host "按回车退出"
