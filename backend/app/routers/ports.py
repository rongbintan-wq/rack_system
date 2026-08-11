"""端口与线缆路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import Device
from app.schemas import ConnectionCreate, ConnectionOut, PortCreate, PortOut, Resp
from app.security import require_user

router = APIRouter(tags=["ports"])


@router.get("/api/devices/{device_id}/ports", response_model=Resp)
def list_ports(device_id: int, db: Session = Depends(get_db)):
    dev = crud.get_device(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    ports = crud.list_ports(db, device_id)
    return Resp(data=[PortOut.model_validate(p).model_dump() for p in ports])


@router.post("/api/ports", response_model=Resp)
def create_port(payload: PortCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    dev = crud.get_device(db, payload.device_id)
    if not dev:
        raise HTTPException(status_code=400, detail="设备不存在")
    p = crud.create_port(db, payload.model_dump(), operator=user)
    db.commit()
    db.refresh(p)
    return Resp(data=PortOut.model_validate(p).model_dump(), msg="端口已添加")


@router.delete("/api/ports/{port_id}", response_model=Resp)
def delete_port(port_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    p = db.query(crud.Port).filter(crud.Port.id == port_id, crud.Port.is_deleted.is_(False)).first()
    if not p:
        raise HTTPException(status_code=404, detail="端口不存在")
    crud.soft_delete_port(db, p, operator=user)
    db.commit()
    return Resp(msg="端口已删除（软删）")


@router.get("/api/connections", response_model=Resp)
def list_connections(db: Session = Depends(get_db)):
    return Resp(data=[ConnectionOut.model_validate(c).model_dump() for c in crud.list_connections(db)])


@router.post("/api/connections", response_model=Resp)
def create_connection(payload: ConnectionCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    c = crud.create_connection(db, payload.model_dump(), operator=user)
    db.commit()
    db.refresh(c)
    return Resp(data=ConnectionOut.model_validate(c).model_dump(), msg="线缆连接已创建")


@router.delete("/api/connections/{conn_id}", response_model=Resp)
def delete_connection(conn_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    c = db.query(crud.Connection).filter(crud.Connection.id == conn_id, crud.Connection.is_deleted.is_(False)).first()
    if not c:
        raise HTTPException(status_code=404, detail="线缆不存在")
    crud.soft_delete_connection(db, c, operator=user)
    db.commit()
    return Resp(msg="线缆已删除（软删）")
