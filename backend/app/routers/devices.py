"""设备路由：上架 / 编辑 / 下架 / 软删。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from urllib.parse import quote

from openpyxl import Workbook

from app.database import get_db
from app import crud
from app.models import Device, Rack
from app.schemas import (
    DeviceCreate,
    DeviceMountReq,
    DeviceOut,
    DeviceUpdate,
    Resp,
)
from app.security import require_user

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _check_rack(db: Session, rack_code: str) -> Rack:
    rack = crud.get_rack_by_code(db, rack_code)
    if not rack:
        raise HTTPException(status_code=400, detail=f"机柜编号「{rack_code}」不存在")
    return rack


@router.get("", response_model=Resp)
def list_devices(rack_code: str = None, rack_id: int = None, db: Session = Depends(get_db)):
    devs = crud.list_devices(db, rack_code=rack_code, rack_id=rack_id)
    return Resp(data=[DeviceOut.model_validate(d).model_dump() for d in devs])


@router.post("", response_model=Resp)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), user=Depends(require_user)):
    rack = _check_rack(db, payload.rack_code)
    # U 越界
    end_u = payload.start_u + payload.height_u - 1
    if payload.start_u < 1 or end_u > rack.height_u:
        raise HTTPException(status_code=400, detail=f"起始U位 {payload.start_u} + 占用U数 {payload.height_u} 超出机柜总高度 {rack.height_u}U")
    # 冲突
    conflict = _conflict(db, rack.rack_code, payload.start_u, payload.height_u, exclude_id=None)
    if conflict:
        raise HTTPException(status_code=400, detail=f"U 位冲突：与资源编号 {conflict} ")
    dev = crud.create_device(db, payload.model_dump(), operator=user)
    db.commit()
    db.refresh(dev)
    return Resp(data=DeviceOut.model_validate(dev).model_dump(), msg="设备已上架")


@router.post("/mount", response_model=Resp)
def mount_device(payload: DeviceMountReq, db: Session = Depends(get_db), user=Depends(require_user)):
    """点击空闲U位的上架入口。"""
    return create_device(DeviceCreate(**payload.model_dump()), db=db, user=user)


EXPORT_HEADERS = [
    "资源ID", "资源编号", "设备类型", "品牌名称", "型号", "区域省份城市场地",
    "机房名称", "机柜名称", "机柜编号", "起始U位", "占用U位数", "资产状态",
    "SN序列号", "主机名",
]


@router.get("/export")
def export_devices(db: Session = Depends(get_db)):
    """一次性导出所有未删除设备为 Excel（与导入模板列对齐，便于回导）。"""
    devs = (
        db.query(Device)
        .filter(Device.is_deleted.is_(False))
        .order_by(Device.room_name, Device.rack_code, Device.start_u)
        .all()
    )
    wb = Workbook()
    ws = wb.active
    ws.title = "设备"
    ws.append(EXPORT_HEADERS)
    for d in devs:
        ws.append([
            d.resource_id, d.resource_code, d.device_type, d.brand_name, d.model, d.region,
            d.room_name, d.rack_name, d.rack_code, d.start_u, d.height_u, d.asset_status,
            d.sn, d.hostname,
        ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = "设备导出.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=devices_export.xlsx; filename*=UTF-8''{quote(fname)}"
        },
    )


@router.get("/{device_id}", response_model=Resp)
def get_device(device_id: int, db: Session = Depends(get_db)):
    dev = crud.get_device(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    return Resp(data=DeviceOut.model_validate(dev).model_dump())


@router.put("/{device_id}", response_model=Resp)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db), user=Depends(require_user)):
    dev = crud.get_device(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    # 若改 U 位/机柜，需重检冲突与越界
    new_rack_code = data.get("rack_code", dev.rack_code)
    new_start = data.get("start_u", dev.start_u)
    new_height = data.get("height_u", dev.height_u)
    rack = _check_rack(db, new_rack_code)
    end_u = new_start + new_height - 1
    if new_start < 1 or end_u > rack.height_u:
        raise HTTPException(status_code=400, detail="U 位越界")
    conflict = _conflict(db, new_rack_code, new_start, new_height, exclude_id=dev.id)
    if conflict:
        raise HTTPException(status_code=400, detail=f"U 位冲突：与资源编号 {conflict}")
    crud.update_device(db, dev, data, operator=user)
    db.commit()
    return Resp(data=DeviceOut.model_validate(dev).model_dump(), msg="设备更新成功")


@router.post("/{device_id}/decommission", response_model=Resp)
def decommission(device_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    dev = crud.get_device(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    crud.decommission_device(db, dev, operator=user)
    db.commit()
    return Resp(data=DeviceOut.model_validate(dev).model_dump(), msg="设备已下架")


@router.delete("/{device_id}", response_model=Resp)
def delete_device(device_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    dev = crud.get_device(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    crud.soft_delete_device(db, dev, operator=user)
    db.commit()
    return Resp(msg="设备已删除（软删）")


def _conflict(db: Session, rack_code: str, start_u: int, height_u: int, exclude_id: int | None) -> str | None:
    end_u = start_u + height_u - 1
    for d in db.query(Device).filter(Device.rack_code == rack_code, Device.is_deleted.is_(False)):
        if exclude_id and d.id == exclude_id:
            continue
        if max(start_u, d.start_u) <= min(end_u, d.start_u + d.height_u - 1):
            return d.resource_code
    return None
