"""机房路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import Room
from app.schemas import (
    Resp,
    RoomCreate,
    RoomStatOut,
    RoomUpdate,
)
from app.security import require_user

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


def _room_out(db: Session, room: Room) -> dict:
    d = RoomStatOut.model_validate(room).model_dump()
    d.update(crud.room_stats(db, room))
    return d


@router.get("", response_model=Resp)
def list_rooms(region: str = None, city: str = None, status: str = None, db: Session = Depends(get_db)):
    rows = crud.list_rooms(db, region=region, city=city, status=status)
    return Resp(data=[_room_out(db, r) for r in rows])


@router.post("", response_model=Resp)
def create_room(payload: RoomCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    exists = db.query(Room).filter(Room.room_name == payload.room_name, Room.is_deleted.is_(False)).first()
    if exists:
        raise HTTPException(status_code=400, detail=f"机房名称「{payload.room_name}」已存在")
    room = crud.create_room(db, payload.model_dump(), operator=user)
    db.commit()
    db.refresh(room)
    return Resp(data=_room_out(db, room), msg="机房创建成功")


@router.get("/{room_id}", response_model=Resp)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="机房不存在")
    return Resp(data=_room_out(db, room))


@router.put("/{room_id}", response_model=Resp)
def update_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db), user=Depends(require_user)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="机房不存在")
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    crud.update_room(db, room, data, operator=user)
    db.commit()
    return Resp(data=_room_out(db, room), msg="机房更新成功")


@router.delete("/{room_id}", response_model=Resp)
def delete_room(room_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="机房不存在")
    crud.soft_delete_room(db, room, operator=user)
    db.commit()
    return Resp(msg="机房已删除（软删）")


@router.get("/{room_id}/racks", response_model=Resp)
def room_racks(room_id: int, db: Session = Depends(get_db)):
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="机房不存在")
    return Resp(data=[_rack_out(db, r) for r in crud.list_racks(db, room_id=room_id)])


@router.get("/{room_id}/device-types", response_model=Resp)
def room_device_types(room_id: int, db: Session = Depends(get_db)):
    """按设备类型聚合（机房详情页饼图/柱状图）。"""
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="机房不存在")
    racks = crud.list_racks(db, room_id=room_id)
    codes = [r.rack_code for r in racks]
    agg = {}
    total = 0
    if codes:
        rows = (
            db.query(crud.Device.device_type, crud.Device.asset_status)
            .filter(crud.Device.rack_code.in_(codes), crud.Device.is_deleted.is_(False))
            .all()
        )
        for dtype, astatus in rows:
            agg.setdefault(dtype, {"count": 0, "running": 0})
            agg[dtype]["count"] += 1
            if astatus == "运行中":
                agg[dtype]["running"] += 1
            total += 1
    return Resp(data={"total": total, "by_type": agg})


def _rack_out(db: Session, rack) -> dict:
    from app.schemas import RackStatOut
    from app.models import Rack
    d = RackStatOut.model_validate(rack).model_dump()
    room = db.query(Room).filter(Room.id == rack.room_id).first()
    d["room_name"] = room.room_name if room else ""
    d.update(crud.rack_stats(db, rack))
    return d
