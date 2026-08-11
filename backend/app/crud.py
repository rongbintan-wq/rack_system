"""CRUD 封装：所有增删改的唯一入口（DB 变更铁律）。

- 严禁物理 DELETE：删除统一置 is_deleted=True。
- 关键操作写审计日志 audit_log。
- 批量导入使用事务（见 importer.py）。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Connection,
    Device,
    ImportLog,
    Port,
    Rack,
    Room,
    User,
)


# ----------------------------- 审计日志 -----------------------------
def log_audit(
    db: Session,
    operator: Optional[User],
    action: str,
    resource_type: str,
    resource_id: int = 0,
    detail: str = "",
) -> None:
    db.add(
        AuditLog(
            operator_id=operator.id if operator else 0,
            operator_name=operator.display_name or (operator.username if operator else "system"),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
        )
    )


# ----------------------------- Room -----------------------------
def get_room(db: Session, room_id: int) -> Optional[Room]:
    return db.query(Room).filter(Room.id == room_id, Room.is_deleted.is_(False)).first()


def list_rooms(db: Session, region: str = None, city: str = None, status: str = None):
    q = db.query(Room).filter(Room.is_deleted.is_(False))
    if region:
        q = q.filter(Room.region == region)
    if city:
        q = q.filter(Room.city == city)
    if status:
        q = q.filter(Room.status == status)
    return q.order_by(Room.id).all()


def create_room(db: Session, data: dict, operator: Optional[User] = None) -> Room:
    room = Room(**data)
    db.add(room)
    db.flush()
    log_audit(db, operator, "create", "room", room.id, json.dumps(data, ensure_ascii=False))
    return room


def update_room(db: Session, room: Room, data: dict, operator: Optional[User] = None) -> Room:
    before = {k: getattr(room, k) for k in data}
    for k, v in data.items():
        setattr(room, k, v)
    log_audit(
        db,
        operator,
        "update",
        "room",
        room.id,
        json.dumps({"before": before, "after": data}, ensure_ascii=False),
    )
    return room


def soft_delete_room(db: Session, room: Room, operator: Optional[User] = None) -> None:
    # 级联软删其下机柜与设备
    for rack in db.query(Rack).filter(Rack.room_id == room.id, Rack.is_deleted.is_(False)):
        rack.is_deleted = True
        for dev in db.query(Device).filter(Device.rack_code == rack.rack_code, Device.is_deleted.is_(False)):
            dev.is_deleted = True
    room.is_deleted = True
    log_audit(db, operator, "delete", "room", room.id, f"软删机房 {room.room_name}")


def room_stats(db: Session, room: Room) -> dict:
    racks = db.query(Rack).filter(Rack.room_id == room.id, Rack.is_deleted.is_(False)).all()
    total = len(racks)
    occupied = 0
    device_count = 0
    for r in racks:
        devs = db.query(Device).filter(Device.rack_code == r.rack_code, Device.is_deleted.is_(False)).all()
        device_count += len(devs)
        if devs:
            occupied += 1
    free = total - occupied
    usage = round(occupied / total * 100, 1) if total else 0.0
    return {
        "occupied_racks": occupied,
        "free_racks": free,
        "usage_rate": usage,
        "device_count": device_count,
    }


# ----------------------------- Rack -----------------------------
def get_rack(db: Session, rack_id: int) -> Optional[Rack]:
    return db.query(Rack).filter(Rack.id == rack_id, Rack.is_deleted.is_(False)).first()


def get_rack_by_code(db: Session, rack_code: str) -> Optional[Rack]:
    return db.query(Rack).filter(Rack.rack_code == rack_code, Rack.is_deleted.is_(False)).first()


def list_racks(db: Session, room_id: int = None):
    q = db.query(Rack).filter(Rack.is_deleted.is_(False))
    if room_id:
        q = q.filter(Rack.room_id == room_id)
    return q.order_by(Rack.id).all()


def create_rack(db: Session, data: dict, operator: Optional[User] = None) -> Rack:
    rack = Rack(**data)
    db.add(rack)
    db.flush()
    log_audit(db, operator, "create", "rack", rack.id, json.dumps(data, ensure_ascii=False))
    return rack


def update_rack(db: Session, rack: Rack, data: dict, operator: Optional[User] = None) -> Rack:
    before = {k: getattr(rack, k) for k in data}
    for k, v in data.items():
        setattr(rack, k, v)
    log_audit(db, operator, "update", "rack", rack.id, json.dumps({"before": before, "after": data}, ensure_ascii=False))
    return rack


def soft_delete_rack(db: Session, rack: Rack, operator: Optional[User] = None) -> None:
    for dev in db.query(Device).filter(Device.rack_code == rack.rack_code, Device.is_deleted.is_(False)):
        dev.is_deleted = True
    rack.is_deleted = True
    log_audit(db, operator, "delete", "rack", rack.id, f"软删机柜 {rack.rack_code}")


def rack_used_u(db: Session, rack_code: str, exclude_id: int = None) -> int:
    """计算机柜已占用 U 数（按 U 位区间并集，去重）。"""
    q = db.query(Device).filter(Device.rack_code == rack_code, Device.is_deleted.is_(False))
    if exclude_id:
        q = q.filter(Device.id != exclude_id)
    devs = q.all()
    if not devs:
        return 0
    intervals = sorted([(d.start_u, d.start_u + d.height_u - 1) for d in devs])
    used = 0
    cur_s, cur_e = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_e + 1:
            cur_e = max(cur_e, e)
        else:
            used += cur_e - cur_s + 1
            cur_s, cur_e = s, e
    used += cur_e - cur_s + 1
    return used


def rack_stats(db: Session, rack: Rack) -> dict:
    used = rack_used_u(db, rack.rack_code)
    cnt = (
        db.query(func.count(Device.id))
        .filter(Device.rack_code == rack.rack_code, Device.is_deleted.is_(False))
        .scalar()
        or 0
    )
    usage = round(used / rack.height_u * 100, 1) if rack.height_u else 0.0
    return {"used_u": used, "usage_rate": usage, "device_count": cnt}


# ----------------------------- Device -----------------------------
def get_device(db: Session, device_id: int) -> Optional[Device]:
    return db.query(Device).filter(Device.id == device_id, Device.is_deleted.is_(False)).first()


def get_device_by_resource_code(db: Session, resource_code: str) -> Optional[Device]:
    return (
        db.query(Device)
        .filter(Device.resource_code == resource_code, Device.is_deleted.is_(False))
        .first()
    )


def list_devices(db: Session, rack_code: str = None, rack_id: int = None):
    q = db.query(Device).filter(Device.is_deleted.is_(False))
    if rack_code:
        q = q.filter(Device.rack_code == rack_code)
    elif rack_id:
        rack = get_rack(db, rack_id)
        if rack:
            q = q.filter(Device.rack_code == rack.rack_code)
    return q.order_by(Device.start_u).all()


def create_device(db: Session, data: dict, operator: Optional[User] = None) -> Device:
    dev = Device(**data)
    db.add(dev)
    db.flush()
    log_audit(db, operator, "create", "device", dev.id, json.dumps(data, ensure_ascii=False))
    return dev


def update_device(db: Session, dev: Device, data: dict, operator: Optional[User] = None) -> Device:
    before = {k: getattr(dev, k) for k in data}
    for k, v in data.items():
        setattr(dev, k, v)
    log_audit(db, operator, "update", "device", dev.id, json.dumps({"before": before, "after": data}, ensure_ascii=False))
    return dev


def soft_delete_device(db: Session, dev: Device, operator: Optional[User] = None) -> None:
    dev.is_deleted = True
    log_audit(db, operator, "delete", "device", dev.id, f"软删设备 {dev.resource_code}")


def decommission_device(db: Session, dev: Device, operator: Optional[User] = None) -> Device:
    """下架：不删除，仅置资产状态为已下架。"""
    before = dev.asset_status
    dev.asset_status = "已下架"
    log_audit(db, operator, "decommission", "device", dev.id, json.dumps({"before": {"asset_status": before}, "after": {"asset_status": "已下架"}}, ensure_ascii=False))
    return dev


# ----------------------------- Port -----------------------------
def list_ports(db: Session, device_id: int):
    return db.query(Port).filter(Port.device_id == device_id, Port.is_deleted.is_(False)).order_by(Port.id).all()


def create_port(db: Session, data: dict, operator: Optional[User] = None) -> Port:
    p = Port(**data)
    db.add(p)
    db.flush()
    log_audit(db, operator, "create", "port", p.id, json.dumps(data, ensure_ascii=False))
    return p


def soft_delete_port(db: Session, p: Port, operator: Optional[User] = None) -> None:
    p.is_deleted = True
    log_audit(db, operator, "delete", "port", p.id, f"软删端口 {p.port_name}")


# ----------------------------- Connection -----------------------------
def list_connections(db: Session):
    return db.query(Connection).filter(Connection.is_deleted.is_(False)).order_by(Connection.id).all()


def create_connection(db: Session, data: dict, operator: Optional[User] = None) -> Connection:
    c = Connection(**data)
    db.add(c)
    db.flush()
    log_audit(db, operator, "create", "connection", c.id, json.dumps(data, ensure_ascii=False))
    return c


def soft_delete_connection(db: Session, c: Connection, operator: Optional[User] = None) -> None:
    c.is_deleted = True
    log_audit(db, operator, "delete", "connection", c.id, "软删线缆")


# ----------------------------- ImportLog -----------------------------
def create_import_log(db: Session, data: dict) -> ImportLog:
    log = ImportLog(**data)
    db.add(log)
    db.flush()
    return log
