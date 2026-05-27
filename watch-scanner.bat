@echo off
title 漏洞预判引擎 — 实时文件监控
echo === 实时扫描监控已启动 ===
echo 监控目录: D:\gas-station\server
echo 检测到文件变更后自动触发扫描
echo.

setlocal enabledelayedexpansion
set SCANNER=D:\.ai-memory\scripts\code-scanner.py
set WATCH_DIR=D:\gas-station\server
set CACHE_FILE=%TEMP%\scanner-file-list.txt

:watch
:: 记录当前文件列表和修改时间
dir /s /b %WATCH_DIR%\*.js 2>nul > %CACHE_FILE%.new
if not exist %CACHE_FILE% (
    copy %CACHE_FILE%.new %CACHE_FILE% >nul
    goto :sleep
)

:: 比较文件列表是否变化
fc %CACHE_FILE% %CACHE_FILE%.new >nul 2>nul
if errorlevel 1 (
    echo [%date% %time%] 检测到文件变更...
    copy %CACHE_FILE%.new %CACHE_FILE% >nul
    python3 %SCANNER% %WATCH_DIR%
    echo ---
)

:sleep
timeout /t 10 /nobreak >nul
goto :watch
