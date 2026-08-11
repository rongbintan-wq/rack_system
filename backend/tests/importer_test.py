"""导入核心算法测试：U 位冲突检测 / 排除自身 UPDATE / 越界 / 幂等。"""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")

from app.database import Base, SessionLocal, engine
from app import crud, models
from app.importer import extract_rows, validate_rows
from openpyxl import Workbook


def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    ws.append(["资源ID", "资源编号", "设备类型", "品牌名称", "型号", "区域省份城市场地",
               "机房名称", "机柜名称", "机柜编号", "起始U位", "占用U位数", "资产状态", "SN", "主机名"])
    for r in rows:
        ws.append(r)
    import io
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def setup_module(_):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    room = models.Room(room_name="测试机房", region="华南", province="广东", city="深圳")
    db.add(room)
    db.flush()
    rack = models.Rack(rack_name="A01", rack_code="RACK-A01-99", room_id=room.id, height_u=42)
    db.add(rack)
    db.flush()
    db.add(models.Device(resource_code="EXIST-1", device_type="交换机", rack_code="RACK-A01-99", start_u=10, height_u=2, model="X1"))
    db.commit()
    db.close()


def test_u_conflict_detected():
    db = SessionLocal()
    rows = extract_rows(_xlsx([["R1", "NEW-1", "交换机", "华为", "S1", "华南广东深圳", "测试机房", "A01", "RACK-A01-99", 11, 1, "运行中", "", ""]]))
    valid, errors = validate_rows(db, rows)
    db.close()
    assert len(errors) == 1
    assert "冲突" in errors[0]["reason"]


def test_self_update_excluded():
    """同一资源编号改 U 位，旧记录应排除，不报冲突。"""
    db = SessionLocal()
    rows = extract_rows(_xlsx([["R1", "EXIST-1", "交换机", "华为", "X1", "华南广东深圳", "测试机房", "A01", "RACK-A01-99", 20, 2, "运行中", "", ""]]))
    valid, errors = validate_rows(db, rows)
    db.close()
    assert errors == []
    assert valid[0].action == "update"


def test_u_out_of_bounds():
    db = SessionLocal()
    rows = extract_rows(_xlsx([["R1", "NEW-2", "交换机", "华为", "S1", "华南广东深圳", "测试机房", "A01", "RACK-A01-99", 42, 2, "运行中", "", ""]]))
    valid, errors = validate_rows(db, rows)
    db.close()
    assert any("超出" in e["reason"] for e in errors)


def test_missing_rack():
    db = SessionLocal()
    rows = extract_rows(_xlsx([["R1", "NEW-3", "交换机", "华为", "S1", "华南广东深圳", "测试机房", "A01", "RACK-NOPE", 1, 1, "运行中", "", ""]]))
    valid, errors = validate_rows(db, rows)
    db.close()
    assert any("不存在" in e["reason"] for e in errors)
