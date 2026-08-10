"""生成 Excel 设备导入模板与示例数据（openpyxl）。"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

HEADERS = [
    "资源ID", "资源编号", "设备类型", "品牌名称", "型号",
    "区域省份城市场地", "机房名称", "机柜名称", "机柜编号",
    "起始U位", "占用U位数", "资产状态", "SN序列号", "主机名",
]

# 附录 A 测试数据
SAMPLE_ROWS = [
    ["RES-001", "ASSET-SZ-001", "交换机", "华为(HUAWEI)", "S5731-S48T4X", "华南广东深圳新浩e都", "开放区01机房", "A01", "RACK-A01-01", 1, 1, "运行中", "", "core-sw-01"],
    ["RES-002", "ASSET-SZ-002", "交换机", "华为(HUAWEI)", "S5735-L24P4X-A", "华南广东深圳新浩e都", "开放区01机房", "A01", "RACK-A01-01", 3, 1, "运行中", "", ""],
    ["RES-003", "ASSET-SZ-003", "交换机", "华为(HUAWEI)", "S6730-H24X6C", "华南广东深圳新浩e都", "开放区01机房", "A01", "RACK-A01-01", 5, 2, "运行中", "", ""],
    ["RES-004", "ASSET-SZ-004", "交换机", "华为(HUAWEI)", "S5732-H24UM2XC", "华南广东深圳新浩e都", "开放区01机房", "A01", "RACK-A01-01", 8, 1, "运行中", "", ""],
    ["RES-005", "ASSET-SZ-005", "交换机", "华为(HUAWEI)", "S5735-L48T4S-A", "华南广东深圳新浩e都", "开放区01机房", "A01", "RACK-A01-01", 10, 2, "运行中", "", ""],
    ["RES-006", "ASSET-SZ-006", "交换机", "华为(HUAWEI)", "S5731-S48T4X", "华南广东深圳新浩e都", "开放区01机房", "A02", "RACK-A02-01", 1, 1, "运行中", "", ""],
    ["RES-007", "ASSET-SZ-007", "交换机", "华为(HUAWEI)", "S6730-H24X6C", "华南广东深圳新浩e都", "开放区01机房", "A02", "RACK-A02-01", 3, 2, "运行中", "", ""],
    ["RES-008", "ASSET-SZ-008", "服务器", "DELL", "R740", "华南广东深圳新浩e都", "开放区02机房", "B01", "RACK-B01-01", 1, 2, "运行中", "", ""],
    ["RES-009", "ASSET-SZ-009", "服务器", "DELL", "R650", "华南广东深圳新浩e都", "开放区02机房", "B01", "RACK-B01-01", 4, 2, "运行中", "", ""],
    ["RES-010", "ASSET-SZ-010", "防火墙", "华为(HUAWEI)", "USG6630", "华南广东深圳新浩e都", "荣耀机房", "C01", "RACK-C01-01", 1, 1, "运行中", "", ""],
]


def _write(wb: Workbook, rows) -> None:
    ws = wb.active
    ws.title = "设备导入"
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)


def build_template(path: Path) -> None:
    wb = Workbook()
    # 模板：表头 + 1 行示例（用户照填）
    _write(wb, [SAMPLE_ROWS[0]])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def build_sample(path: Path) -> None:
    wb = Workbook()
    _write(wb, SAMPLE_ROWS)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
