检查 Gateway 是否运行：`netstat -ano | grep 18789` 看有没有 LISTENING。如果没有，运行 `powershell -ExecutionPolicy Bypass -File "D:\OpenClaw\gateway-boot.ps1"` 启动。然后 `openclaw status` 确认微信通道正常。
