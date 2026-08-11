// SVG 机柜视图坐标与颜色工具（与后端 app/utils/svg.py 保持一致）
// 坐标公式（U1 在底部，Y 轴向下，含 +1 off-by-one 修正）：
//   设备块顶边 Y = 上边距 + (rack.height_u - start_u - height_u + 1) × 每U像素
//   设备块高度   = height_u × 每U像素

export const U_HEIGHT = 22
export const TOP_MARGIN = 10
export const BOTTOM_MARGIN = 10
export const RACK_WIDTH = 140

export const DEVICE_COLORS = {
  交换机: '#50E3C2',
  服务器: '#4A90E2',
  防火墙: '#F5A623',
  路由器: '#BD10E0',
  存储: '#7ED321',
  KVM: '#9B9B9B',
  其他: '#9B9B9B',
}
export const FREE_COLOR = '#F5F5F5'
export const RESERVED_COLOR = '#F8E71C'

export function deviceColor(type) {
  return DEVICE_COLORS[type] || DEVICE_COLORS['其他']
}

export function rackCanvasHeight(heightU) {
  return heightU * U_HEIGHT + TOP_MARGIN + BOTTOM_MARGIN
}

export function deviceBlockY(heightU, startU, devHeightU) {
  return TOP_MARGIN + (heightU - startU - devHeightU + 1) * U_HEIGHT
}

export function deviceBlockHeight(devHeightU) {
  return devHeightU * U_HEIGHT
}

// 生成某个机柜的空闲 U 位块（用于点击上架预填）
export function freeUnits(devices, heightU) {
  const occupied = Array(heightU + 1).fill(false)
  for (const d of devices) {
    for (let u = d.start_u; u <= d.end_u; u++) occupied[u] = true
  }
  const free = []
  for (let u = 1; u <= heightU; u++) {
    if (!occupied[u]) free.push(u)
  }
  return free
}
