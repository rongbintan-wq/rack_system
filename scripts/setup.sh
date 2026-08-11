#!/usr/bin/env bash
# 本地研发环境一键初始化（约 3 分钟就绪）
# 用法：bash scripts/setup.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Step 1 ▶ 检查运行环境"
python3 --version >/dev/null 2>&1 || { echo "需要 Python 3.11+"; exit 1; }
node --version >/dev/null 2>&1 || { echo "需要 Node 18+"; exit 1; }

echo "Step 2 ▶ 安装系统依赖（按需，Ubuntu 示例）"
# sudo apt-get install -y gcc default-libmysqlclient-dev 2>/dev/null || true

echo "Step 3 ▶ 安装工具链（uv + pnpm，可选）"
# pip install uv 2>/dev/null || true
# npm install -g pnpm 2>/dev/null || true

echo "Step 4 ▶ 初始化配置"
if [ ! -f "$ROOT/backend/.env.local" ]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env.local"
  echo "   已生成 backend/.env.local（按需修改 DB 连接串 / SECRET_KEY / JWT）"
fi

echo "Step 5 ▶ 安装项目依赖"
cd "$ROOT/backend"
python3 -m venv .venv 2>/dev/null || true
if [ -f ".venv/bin/pip" ]; then PIP=".venv/bin/pip"; else PIP="pip"; fi
$PIP install -q -r requirements.txt 2>/dev/null || $PIP install -q fastapi "uvicorn[standard]" sqlalchemy openpyxl pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart httpx pytest
cd "$ROOT/web"
npm install --no-audit --no-fund

echo "Step 6 ▶ 初始化数据库（建表 + 预置示例数据）"
cd "$ROOT/backend"
if [ -f ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
$PY init_db.py

echo "Step 7 ▶ 启动开发服务"
cd "$ROOT"
echo "   后端将监听 :8000，前端用 'cd web && npm run dev' 启动（默认 :5173）"
echo "   或执行 'bash start.sh' 一并启动前后端"
echo "✅ 初始化完成。"
