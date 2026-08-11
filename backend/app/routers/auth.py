"""认证路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginReq, Resp, Token, UserOut
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Resp)
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.is_deleted.is_(False)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")
    token = create_access_token(user.username)
    return Resp(data=Token(access_token=token).model_dump())


@router.get("/me", response_model=Resp)
def me(user: User = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="未登录")
    return Resp(data=UserOut.model_validate(user).model_dump())
