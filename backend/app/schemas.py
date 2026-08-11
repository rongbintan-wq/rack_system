"""Pydantic schemas：请求/响应模型。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Resp(BaseModel):
    """统一返回格式：{ code, data, msg }。"""
    code: int = 0
    data: object = None
    msg: str = "success"


# ----------------------------- Auth -----------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginReq(BaseModel):
    username: str
    password: str


# ----------------------------- User -----------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool


# ----------------------------- Room -----------------------------
class RoomCreate(BaseModel):
    room_name: str
    building: str = ""
    floor: str = ""
    total_racks: int = 0
    status: str = "在用"
    region: str = ""
    province: str = ""
    city: str = ""
    site: str = ""
    owner: str = ""
    contact_phone: str = ""
    notes: str = ""


class RoomUpdate(BaseModel):
    building: Optional[str] = None
    floor: Optional[str] = None
    total_racks: Optional[int] = None
    status: Optional[str] = None
    region: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    site: Optional[str] = None
    owner: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_name: str
    building: str
    floor: str
    total_racks: int
    status: str
    region: str
    province: str
    city: str
    site: str
    owner: str
    contact_phone: str
    notes: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class RoomStatOut(RoomOut):
    occupied_racks: int = 0
    free_racks: int = 0
    usage_rate: float = 0.0
    device_count: int = 0


# ----------------------------- Rack -----------------------------
class RackCreate(BaseModel):
    rack_name: str
    rack_code: str
    room_id: int
    height_u: int = 42
    width_mm: int = 600
    depth_mm: int = 1000
    power_type: str = "双路市电"
    status: str = "空闲"
    location_note: str = ""
    notes: str = ""


class RackUpdate(BaseModel):
    rack_name: Optional[str] = None
    height_u: Optional[int] = None
    power_type: Optional[str] = None
    status: Optional[str] = None
    location_note: Optional[str] = None
    notes: Optional[str] = None


class RackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rack_name: str
    rack_code: str
    room_id: int
    height_u: int
    width_mm: int
    depth_mm: int
    power_type: str
    status: str
    location_note: str
    notes: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class RackStatOut(RackOut):
    used_u: int = 0
    usage_rate: float = 0.0
    device_count: int = 0
    room_name: str = ""


# ----------------------------- Device -----------------------------
class DeviceCreate(BaseModel):
    resource_id: str = ""
    resource_code: str
    device_type: str
    brand_name: str = ""
    model: str = ""
    region: str = ""
    site_detail: str = ""
    room_name: str = ""
    rack_name: str = ""
    rack_code: str
    start_u: int
    height_u: int = 1
    asset_status: str = "运行中"
    sn: str = ""
    hostname: str = ""


class DeviceUpdate(BaseModel):
    device_type: Optional[str] = None
    brand_name: Optional[str] = None
    model: Optional[str] = None
    rack_code: Optional[str] = None
    start_u: Optional[int] = None
    height_u: Optional[int] = None
    asset_status: Optional[str] = None
    sn: Optional[str] = None
    hostname: Optional[str] = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resource_id: str
    resource_code: str
    device_type: str
    brand_name: str
    model: str
    region: str
    site_detail: str
    room_name: str
    rack_name: str
    rack_code: str
    start_u: int
    height_u: int
    asset_status: str
    sn: str
    hostname: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class DeviceMountReq(BaseModel):
    """上架设备（点击空闲U位预填）。"""
    resource_id: str = ""
    resource_code: str
    device_type: str = "交换机"
    brand_name: str = ""
    model: str = ""
    rack_code: str
    start_u: int
    height_u: int = 1
    asset_status: str = "运行中"
    sn: str = ""
    hostname: str = ""


# ----------------------------- Import -----------------------------
class ImportRowError(BaseModel):
    row: int
    resource_code: str = ""
    reason: str


class ImportPreviewResp(BaseModel):
    total: int
    to_insert: int
    to_update: int
    errors: list[ImportRowError]
    # 预览用的设备占位（含计算后的坐标信息由前端渲染）
    preview_devices: list[dict] = []


class ImportCommitResp(BaseModel):
    total_rows: int
    success_count: int
    failed_count: int
    import_id: int
    errors: list[ImportRowError]
