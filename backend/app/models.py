"""ORM 模型：严格按开发提示语 Schema First 定义，禁止擅自增减字段。

全局约束：
- 所有表均含 created_at / updated_at / is_deleted（软删）。
- 时间字段统一 DATETIME。
- 删除一律软删，禁止物理 DELETE。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)


# ----------------------------------------------------------------------------
# User（RBAC）
# ----------------------------------------------------------------------------
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), default="")
    role: Mapped[str] = mapped_column(String(32), default="guest", nullable=False)  # super_admin|op|guest
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ----------------------------------------------------------------------------
# Room（机房）
# ----------------------------------------------------------------------------
class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    building: Mapped[str] = mapped_column(String(128), default="")
    floor: Mapped[str] = mapped_column(String(64), default="")
    total_racks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="在用")  # 在用/停用/预留
    region: Mapped[str] = mapped_column(String(64), default="")
    province: Mapped[str] = mapped_column(String(64), default="")
    city: Mapped[str] = mapped_column(String(64), default="")
    site: Mapped[str] = mapped_column(String(255), default="")
    owner: Mapped[str] = mapped_column(String(64), default="")
    contact_phone: Mapped[str] = mapped_column(String(64), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    racks: Mapped[list["Rack"]] = relationship(back_populates="room")


# ----------------------------------------------------------------------------
# Rack（机柜）
# ----------------------------------------------------------------------------
class Rack(Base, TimestampMixin):
    __tablename__ = "racks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rack_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 如 A01
    rack_code: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    height_u: Mapped[int] = mapped_column(Integer, default=42, nullable=False)  # 42/45/47/48
    width_mm: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    power_type: Mapped[str] = mapped_column(String(64), default="双路市电")
    status: Mapped[str] = mapped_column(String(32), default="空闲")  # 空闲/部分占用/已满/预留/故障
    location_note: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    room: Mapped["Room"] = relationship(back_populates="racks")
    devices: Mapped[list["Device"]] = relationship(back_populates="rack")


# ----------------------------------------------------------------------------
# Device（设备）—— 严格对应 Excel 导入列
# ----------------------------------------------------------------------------
class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = mapped_column(String(128), index=True, default="")   # Excel A 列
    resource_code: Mapped[str] = mapped_column(String(128), index=True, nullable=False)  # Excel B 列
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)  # 交换机/服务器/防火墙/路由器/存储/KVM/其他
    brand_name: Mapped[str] = mapped_column(String(128), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    region: Mapped[str] = mapped_column(String(255), default="")  # 冗余存储：区域省份城市场地
    site_detail: Mapped[str] = mapped_column(String(255), default="")
    room_name: Mapped[str] = mapped_column(String(128), default="")  # 冗余存储
    rack_name: Mapped[str] = mapped_column(String(64), default="")
    rack_code: Mapped[str] = mapped_column(ForeignKey("racks.rack_code"), nullable=False, index=True)
    start_u: Mapped[int] = mapped_column(Integer, nullable=False)  # 起始U位，从下往上数
    height_u: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 占用U位数
    asset_status: Mapped[str] = mapped_column(String(32), default="运行中")  # 运行中/已下架/维修中/报废
    sn: Mapped[str] = mapped_column(String(128), default="")
    hostname: Mapped[str] = mapped_column(String(128), default="")

    rack: Mapped["Rack"] = relationship(back_populates="devices")
    ports: Mapped[list["Port"]] = relationship(back_populates="device")


# ----------------------------------------------------------------------------
# Port（端口）
# ----------------------------------------------------------------------------
class Port(Base, TimestampMixin):
    __tablename__ = "ports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False, index=True)
    port_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 如 GigE1/0/1
    port_type: Mapped[str] = mapped_column(String(32), default="电口")  # 电口/光口/管理口/Console
    speed: Mapped[str] = mapped_column(String(16), default="1G")  # 10M/100M/1G/10G/25G/40G/100G
    status: Mapped[str] = mapped_column(String(16), default="未接")  # up/down/预留/未接

    device: Mapped["Device"] = relationship(back_populates="ports")


# ----------------------------------------------------------------------------
# Connection（线缆连接）
# ----------------------------------------------------------------------------
class Connection(Base, TimestampMixin):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    port_a_id: Mapped[int] = mapped_column(ForeignKey("ports.id"), nullable=False, index=True)
    port_b_id: Mapped[int] = mapped_column(ForeignKey("ports.id"), nullable=False, index=True)
    cable_type: Mapped[str] = mapped_column(String(32), default="网线-Cat6")  # 光纤-LC/光纤-MPO/网线-Cat6/网线-Cat6A/铜缆-DAC
    length_m: Mapped[float] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


# ----------------------------------------------------------------------------
# ImportLog（导入记录）
# ----------------------------------------------------------------------------
class ImportLog(Base, TimestampMixin):
    __tablename__ = "import_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    import_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="成功")  # 成功/部分成功/失败
    error_detail: Mapped[str] = mapped_column(Text, default="{}")  # JSON：每行错误原因


# ----------------------------------------------------------------------------
# AuditLog（审计日志）
# ----------------------------------------------------------------------------
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(Integer, default=0)
    operator_name: Mapped[str] = mapped_column(String(64), default="")
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # create/update/delete/import/...
    resource_type: Mapped[str] = mapped_column(String(64), default="")  # room/rack/device/...
    resource_id: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="")  # 前后值对比 JSON
