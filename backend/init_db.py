"""初始化数据库：建表 + 预置示例数据（3 机房 / 6 机柜 / 15 设备）。

运行：
    cd backend
    python init_db.py
"""
from __future__ import annotations

from datetime import datetime

from app.database import Base, SessionLocal, engine
from app.models import Device, Rack, Room, User
from app.security import hash_password
from app.config import settings


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 管理员
        if not db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first():
            db.add(
                User(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    display_name="超级管理员",
                    role="super_admin",
                    is_active=True,
                )
            )

        # 机房
        rooms = {
            "开放区01机房": Room(
                room_name="开放区01机房", building="新浩e都A座", floor="04层",
                total_racks=2, status="在用", region="华南", province="广东",
                city="深圳", site="新浩e都A座04层开放区01", owner="张工", contact_phone="13800000001",
            ),
            "开放区02机房": Room(
                room_name="开放区02机房", building="新浩e都A座", floor="04层",
                total_racks=2, status="在用", region="华南", province="广东",
                city="深圳", site="新浩e都A座04层开放区02", owner="李工", contact_phone="13800000002",
            ),
            "荣耀机房": Room(
                room_name="荣耀机房", building="新浩e都B座", floor="05层",
                total_racks=2, status="在用", region="华南", province="广东",
                city="深圳", site="新浩e都B座05层荣耀机房", owner="王工", contact_phone="13800000003",
            ),
        }
        for r in rooms.values():
            if not db.query(Room).filter(Room.room_name == r.room_name).first():
                db.add(r)
        db.flush()

        # 机柜
        racks = [
            Rack(rack_name="A01", rack_code="RACK-A01-01", room_id=rooms["开放区01机房"].id, height_u=42, power_type="双路市电", status="部分占用"),
            Rack(rack_name="A02", rack_code="RACK-A02-01", room_id=rooms["开放区01机房"].id, height_u=42, power_type="双路市电", status="部分占用"),
            Rack(rack_name="B01", rack_code="RACK-B01-01", room_id=rooms["开放区02机房"].id, height_u=42, power_type="UPS", status="部分占用"),
            Rack(rack_name="B02", rack_code="RACK-B02-01", room_id=rooms["开放区02机房"].id, height_u=42, power_type="UPS", status="空闲"),
            Rack(rack_name="C01", rack_code="RACK-C01-01", room_id=rooms["荣耀机房"].id, height_u=42, power_type="双路市电", status="部分占用"),
            Rack(rack_name="C02", rack_code="RACK-C02-01", room_id=rooms["荣耀机房"].id, height_u=42, power_type="双路市电", status="空闲"),
        ]
        for rk in racks:
            if not db.query(Rack).filter(Rack.rack_code == rk.rack_code).first():
                db.add(rk)
        db.flush()

        rack_by_code = {rk.rack_code: rk for rk in db.query(Rack).all()}

        # 设备（附录 A 10 条 + 5 条扩展 = 15 条）
        devices = [
            ("RES-001", "ASSET-SZ-001", "交换机", "华为(HUAWEI)", "S5731-S48T4X", "RACK-A01-01", 1, 1, "运行中", "core-sw-01"),
            ("RES-002", "ASSET-SZ-002", "交换机", "华为(HUAWEI)", "S5735-L24P4X-A", "RACK-A01-01", 3, 1, "运行中", ""),
            ("RES-003", "ASSET-SZ-003", "交换机", "华为(HUAWEI)", "S6730-H24X6C", "RACK-A01-01", 5, 2, "运行中", ""),
            ("RES-004", "ASSET-SZ-004", "交换机", "华为(HUAWEI)", "S5732-H24UM2XC", "RACK-A01-01", 8, 1, "运行中", ""),
            ("RES-005", "ASSET-SZ-005", "交换机", "华为(HUAWEI)", "S5735-L48T4S-A", "RACK-A01-01", 10, 2, "运行中", ""),
            ("RES-006", "ASSET-SZ-006", "交换机", "华为(HUAWEI)", "S5731-S48T4X", "RACK-A02-01", 1, 1, "运行中", ""),
            ("RES-007", "ASSET-SZ-007", "交换机", "华为(HUAWEI)", "S6730-H24X6C", "RACK-A02-01", 3, 2, "运行中", ""),
            ("RES-008", "ASSET-SZ-008", "服务器", "DELL", "R740", "RACK-B01-01", 1, 2, "运行中", ""),
            ("RES-009", "ASSET-SZ-009", "服务器", "DELL", "R650", "RACK-B01-01", 4, 2, "运行中", ""),
            ("RES-010", "ASSET-SZ-010", "防火墙", "华为(HUAWEI)", "USG6630", "RACK-C01-01", 1, 1, "运行中", "fw-core-01"),
            # 扩展 5 条
            ("RES-011", "ASSET-SZ-011", "交换机", "华为(HUAWEI)", "S5735-L24P4X-A", "RACK-A03-01" if "RACK-A03-01" in rack_by_code else "RACK-A02-01", 10, 1, "运行中", ""),
            ("RES-012", "ASSET-SZ-012", "服务器", "DELL", "R650", "RACK-B02-01", 1, 2, "运行中", ""),
            ("RES-013", "ASSET-SZ-013", "防火墙", "华为(HUAWEI)", "USG6630", "RACK-C02-01", 1, 1, "运行中", ""),
            ("RES-014", "ASSET-SZ-014", "路由器", "华为(HUAWEI)", "NE40E", "RACK-C01-01", 3, 1, "运行中", "core-rt-01"),
            ("RES-015", "ASSET-SZ-015", "存储", "DELL", "EMC Unity", "RACK-B01-01", 7, 2, "运行中", ""),
        ]
        for (rid, code, dtype, brand, model, rc, su, hu, astatus, host) in devices:
            if not db.query(Device).filter(Device.resource_code == code).first():
                rk = rack_by_code.get(rc)
                if not rk:
                    continue
                db.add(
                    Device(
                        resource_id=rid, resource_code=code, device_type=dtype,
                        brand_name=brand, model=model, region="华南广东深圳新浩e都",
                        site_detail=rk.rack_name, room_name=rk.room.room_name if rk.room else "",
                        rack_name=rk.rack_name, rack_code=rc, start_u=su, height_u=hu,
                        asset_status=astatus, hostname=host, sn=f"SN-{code}",
                    )
                )
        db.commit()
        print("✅ 数据库初始化完成：3 机房 / 6 机柜 / 15 设备 / 1 管理员")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
