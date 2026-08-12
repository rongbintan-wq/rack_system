"""FastAPI 应用入口。"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routers import auth, devices, import_, racks, rooms
from app.schemas import Resp
from app.security import hash_password

app = FastAPI(title=settings.APP_NAME, version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (rooms.router, racks.router, devices.router, import_.router, auth.router):
    app.include_router(r)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=Resp(code=exc.status_code, msg=str(exc.detail)).model_dump())


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content=Resp(code=500, msg=f"服务器内部错误：{exc}").model_dump())


@app.get("/api/health", response_model=Resp)
def health():
    return Resp(data={"env": settings.ENV, "require_auth": settings.REQUIRE_AUTH})


# ----------------- 文件下载：Excel 模板 / 示例数据 -----------------
DATA_DIR = BASE_DIR / "data"


@app.get("/api/files/template")
def download_template():
    path = DATA_DIR / "设备导入模板.xlsx"
    if not path.exists():
        from app.excel_template import build_template
        build_template(path)
    return FileResponse(str(path), filename="设备导入模板.xlsx")


@app.get("/api/files/sample")
def download_sample():
    path = DATA_DIR / "示例设备数据.xlsx"
    if not path.exists():
        from app.excel_template import build_sample
        build_sample(path)
    return FileResponse(str(path), filename="示例设备数据.xlsx")


# ----------------- 托管前端构建产物（若存在） -----------------
DIST = BASE_DIR.parent / "web" / "dist"
if DIST.exists():
    assets_dir = DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def spa_index(full_path: str):
        # API 与文件下载交给各自路由；其余路径回退到 SPA 入口（支持 deep-link）
        if full_path.startswith("api") or full_path.startswith("files"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(str(DIST / "index.html"))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_admin()


def _seed_admin():
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not u:
            db.add(
                User(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    display_name="超级管理员",
                    role="super_admin",
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()
