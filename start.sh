#!/usr/bin/env bash
# 一键启动：后端（FastAPI :8000）+ 前端（Vite :5173，代理 /api）
# 用法：bash start.sh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
WEB="$ROOT/web"
LOG="$ROOT/logs"
mkdir -p "$LOG"

echo "▶ 启动后端 (http://127.0.0.1:8000)"
cd "$BACKEND"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info > "$LOG/api.log" 2>&1 &
API_PID=$!
echo "  backend pid=$API_PID"

echo "▶ 启动前端 (http://127.0.0.1:5173)"
cd "$WEB"
npm run dev > "$LOG/web.log" 2>&1 &
WEB_PID=$!
echo "  web pid=$WEB_PID"

echo "✅ 已启动。访问 http://127.0.0.1:5173 （API: http://127.0.0.1:8000/api/health）"
echo "   日志：logs/api.log  logs/web.log"
echo "   停止：kill $API_PID $WEB_PID"
wait
