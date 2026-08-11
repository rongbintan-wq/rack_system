@echo off
chcp 65001 >nul
REM ============================================================
REM  机柜管理系统 - 停止后端服务（释放 8000 端口）
REM  用法（在 CMD 中）： stop.bat
REM ============================================================
echo 查找占用 8000 的进程...
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
  echo   终止 PID %%a
  taskkill /PID %%a /F >nul 2>&1
  set "FOUND=1"
)
if "%FOUND%"=="0" ( echo 未发现监听 8000 的进程 ) else ( echo 已尝试停止。 )
