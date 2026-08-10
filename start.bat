@echo off
chcp 65001 >nul
setlocal
REM ============================================================
REM  机柜管理系统 - Windows 一键启动（FastAPI 同端口托管前端）
REM  用法（在 CMD 中）： start.bat
REM  后端 :8000 同时托管前端 dist，浏览器直接访问根路径即可
REM ============================================================
set "ROOT=C:\Users\Administrator\rack_system"
set "PY=C:\Users\Administrator\.workbuddy\binaries\python\envs\rack\Scripts\python.exe"

echo 检查端口 8000...
netstat -ano 2>nul | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo 端口 8000 已被占用，服务可能已在运行。
  echo 访问： http://127.0.0.1:8000
  echo 如需重启，请先运行 stop.bat。
  goto :eof
)

echo 启动后端（FastAPI 托管前端 dist）...
cd /d "%ROOT%\backend"
start "RackSystem-Backend" "%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
echo 后端已在新窗口启动，稍候数秒后访问： http://127.0.0.1:8000
echo 停止请运行 stop.bat
endlocal
