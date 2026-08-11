@echo off
chcp 65001 >nul
setlocal
REM ============================================================
REM  机柜管理系统 - Windows 一键初始化（无需 bash / Git Bash）
REM  用法（在 CMD 中）： setup.bat
REM  说明：使用本机托管运行时（绝对路径），幂等可重复执行
REM ============================================================
set "ROOT=C:\Users\Administrator\rack_system"
set "PY=C:\Users\Administrator\.workbuddy\binaries\python\envs\rack\Scripts\python.exe"
set "PIP=C:\Users\Administrator\.workbuddy\binaries\python\envs\rack\Scripts\pip.exe"
set "NPM=C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2\npm.cmd"

echo [1/5] 检查托管运行时...
if not exist "%PY%"  ( echo 未找到托管 Python：%PY% & exit /b 1 )
if not exist "%NPM%" ( echo 未找到托管 Node：%NPM% & exit /b 1 )

echo [2/5] 生成配置 .env.local（若不存在）...
if not exist "%ROOT%\backend\.env.local" (
  copy "%ROOT%\backend\.env.example" "%ROOT%\backend\.env.local" >nul
  echo   已复制 backend\.env.local（按需修改 DB 连接串 / SECRET_KEY / JWT）
) else (
  echo   .env.local 已存在，跳过
)

echo [3/5] 安装 Python 依赖（幂等）...
"%PIP%" install -q -r "%ROOT%\backend\requirements.txt"
if errorlevel 1 ( echo pip install 失败 & exit /b 1 )

echo [4/5] 安装前端依赖并构建 dist...
cd /d "%ROOT%\web"
call "%NPM%" install --no-audit --no-fund
if errorlevel 1 ( echo npm install 失败 & exit /b 1 )
call "%NPM%" run build
if errorlevel 1 ( echo npm run build 失败 & exit /b 1 )

echo [5/5] 初始化数据库（建表 + 预置示例数据，幂等）...
cd /d "%ROOT%\backend"
"%PY%" init_db.py
if errorlevel 1 ( echo init_db 失败 & exit /b 1 )

echo.
echo ✅ 初始化完成。运行 start.bat 启动服务。
echo    访问地址： http://127.0.0.1:8000
endlocal
