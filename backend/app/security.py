"""认证与鉴权：JWT + bcrypt。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(sub: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """返回当前用户；若 REQUIRE_AUTH=False 且未携带 token，返回默认管理员（本地联调）。"""
    if not token:
        if not settings.REQUIRE_AUTH:
            admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
            return admin
        return None
    payload = decode_token(token)
    if not payload:
        if not settings.REQUIRE_AUTH:
            admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
            return admin
        return None
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username, User.is_deleted.is_(False)).first()
    return user


def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="未登录或令牌无效")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return user
