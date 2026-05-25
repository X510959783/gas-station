@echo off
title 修复 OpenClaw 符号链接
cd /d "%~dp0"
echo 正在请求管理员权限...
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\gas-station\fix-openclaw.ps1"
pause
