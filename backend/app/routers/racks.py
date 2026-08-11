"""机柜路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import Rack, Room
from app.schemas import (
    DeviceOut,
    Resp,
    RackCreate,
    RackStatOut,
    RackUpdate,
)
from app.security import require_user
from app.utils import svg as svg_util

router = APIRouter(prefix="/api/racks", tags=["racks"])


def _rack_out(db: Session, rack: Rack) -> dict:
    d = RackStatOut.model_validate(rack).model_dump()
    room = db.query(Room).filter(Room.id == rack.room_id).first()
    d["room_name"] = room.room_name if room else ""
    d.update(crud.rack_stats(db, rack))
    return d


@router.get("", response_model=Resp)
def list_racks(room_id: int = None, db: Session = Depends(get_db)):
    rows = crud.list_racks(db, room_id=room_id)
    return Resp(data=[_rack_out(db, r) for r in rows])


@router.post("", response_model=Resp)
def create_rack(payload: RackCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    room = crud.get_room(db, payload.room_id)
    if not room:
        raise HTTPException(status_code=400, detail=f"所属机房 id={payload.room_id} 不存在")
    exists = crud.get_rack_by_code(db, payload.rack_code)
    if exists:
        raise HTTPException(status_code=400, detail=f"机柜编号「{payload.rack_code}」已存在")
    rack = crud.create_rack(db, payload.model_dump(), operator=user)
    db.commit()
    db.refresh(rack)
    # 同步机房 total_racks
    room.total_racks = (
        db.query(Rack).filter(Rack.room_id == room.id, Rack.is_deleted.is_(False)).count()
    )
    db.commit()
    return Resp(data=_rack_out(db, rack), msg="机柜创建成功")


@router.get("/{rack_id}", response_model=Resp)
def get_rack(rack_id: int, db: Session = Depends(get_db)):
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="机柜不存在")
    return Resp(data=_rack_out(db, rack))


@router.put("/{rack_id}", response_model=Resp)
def update_rack(rack_id: int, payload: RackUpdate, db: Session = Depends(get_db), user=Depends(require_user)):
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="机柜不存在")
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    crud.update_rack(db, rack, data, operator=user)
    db.commit()
    return Resp(data=_rack_out(db, rack), msg="机柜更新成功")


@router.delete("/{rack_id}", response_model=Resp)
def delete_rack(rack_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="机柜不存在")
    crud.soft_delete_rack(db, rack, operator=user)
    db.commit()
    return Resp(msg="机柜已删除（软删）")


@router.get("/{rack_id}/devices", response_model=Resp)
def rack_devices(rack_id: int, db: Session = Depends(get_db)):
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="机柜不存在")
    devs = crud.list_devices(db, rack_code=rack.rack_code)
    return Resp(data=[DeviceOut.model_validate(d).model_dump() for d in devs])


@router.get("/{rack_id}/layout", response_model=Resp)
def rack_layout(rack_id: int, db: Session = Depends(get_db)):
    """核心 SVG 布局数据（前端直接渲染）。"""
    rack = crud.get_rack(db, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail="机柜不存在")
    devs = crud.list_devices(db, rack_code=rack.rack_code)
    layout = svg_util.build_rack_layout(rack, devs)
    return Resp(data=layout)
