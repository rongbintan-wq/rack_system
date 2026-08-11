"""SVG 机柜视图坐标与颜色工具（与前端公式保持一致）。

坐标公式（U1 在底部，Y 轴向下，含 +1 off-by-one 修正）：
    设备块顶边 Y = 上边距 + (rack.height_u - start_u - height_u + 1) × 每U像素
    设备块高度   = height_u × 每U像素
"""
from __future__ import annotations

U_HEIGHT = 22          # 每 U 像素
TOP_MARGIN = 10        # 上边距
BOTTOM_MARGIN = 10     # 下边距
RACK_WIDTH = 140       # 视图宽度

DEVICE_COLORS = {
    "交换机": "#50E3C2",
    "服务器": "#4A90E2",
    "防火墙": "#F5A623",
    "路由器": "#BD10E0",
    "存储": "#7ED321",
    "KVM": "#9B9B9B",
    "其他": "#9B9B9B",
}
FREE_COLOR = "#F5F5F5"
RESERVED_COLOR = "#F8E71C"


def device_color(device_type: str) -> str:
    return DEVICE_COLORS.get(device_type, DEVICE_COLORS["其他"])


def rack_canvas_height(height_u: int) -> int:
    return height_u * U_HEIGHT + TOP_MARGIN + BOTTOM_MARGIN


def device_block_y(height_u: int, start_u: int, dev_height_u: int) -> int:
    """设备块顶边 Y 坐标。"""
    return TOP_MARGIN + (height_u - start_u - dev_height_u + 1) * U_HEIGHT


def device_block_height(dev_height_u: int) -> int:
    return dev_height_u * U_HEIGHT


def build_rack_layout(rack, devices) -> dict:
    """返回供前端渲染的结构化机柜布局（后端预计算，前端直接用）。"""
    height_u = rack.height_u
    canvas_h = rack_canvas_height(height_u)
    # 已占用 U 位区间（用于空闲块绘制）
    occupied = []
    for d in devices:
        occupied.append(
            {
                "id": d.id,
                "resource_code": d.resource_code,
                "device_type": d.device_type,
                "brand_name": d.brand_name,
                "model": d.model,
                "hostname": d.hostname,
                "sn": d.sn,
                "asset_status": d.asset_status,
                "start_u": d.start_u,
                "end_u": d.start_u + d.height_u - 1,
                "height_u": d.height_u,
                "y": device_block_y(height_u, d.start_u, d.height_u),
                "h": device_block_height(d.height_u),
                "color": device_color(d.device_type),
            }
        )
    return {
        "rack_code": rack.rack_code,
        "rack_name": rack.rack_name,
        "height_u": height_u,
        "canvas_height": canvas_h,
        "u_height": U_HEIGHT,
        "top_margin": TOP_MARGIN,
        "rack_width": RACK_WIDTH,
        "devices": occupied,
    }
