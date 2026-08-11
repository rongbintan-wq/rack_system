<script setup>
import { computed, ref } from 'vue'
import {
  U_HEIGHT, TOP_MARGIN, RACK_WIDTH,
  deviceColor, rackCanvasHeight, deviceBlockY, deviceBlockHeight,
} from '@/utils/svg'

const props = defineProps({
  rack: { type: Object, required: true },       // { height_u, rack_name, rack_code }
  devices: { type: Array, default: () => [] },   // [{ id, start_u, height_u, device_type, model, brand_name, hostname, resource_code, asset_status }]
  compact: { type: Boolean, default: false },
})
const emit = defineEmits(['select-device', 'mount-u'])

const heightU = computed(() => props.rack.height_u || 42)
const canvasH = computed(() => rackCanvasHeight(heightU.value))
const labelW = computed(() => (props.compact ? 0 : 34))
const svgW = computed(() => RACK_WIDTH + labelW.value + (props.compact ? 8 : 16))
const mainX = computed(() => labelW.value)
const mainW = computed(() => RACK_WIDTH)

// 已占用 U 集合，用于绘制空闲块
const occupied = computed(() => {
  const set = new Set()
  for (const d of props.devices) {
    for (let u = d.start_u; u <= d.start_u + d.height_u - 1; u++) set.add(u)
  }
  return set
})

const uList = computed(() => {
  const arr = []
  for (let u = heightU.value; u >= 1; u--) arr.push(u)
  return arr
})

function blockY(startU, h) {
  return deviceBlockY(heightU.value, startU, h)
}

// 设备块标签：品牌 + 型号（超长截断加省略号）
function devLabel(d) {
  const base = `${d.brand_name || ''} ${d.model || ''}`.trim() || d.resource_code || ''
  const max = props.compact ? 9 : 18
  return base.length > max ? base.slice(0, max - 1) + '…' : base
}

// 自定义 Tooltip
const tip = ref({ show: false, x: 0, y: 0, dev: null })
function onEnterDev(e, dev) {
  const rect = e.currentTarget.ownerSVGElement.getBoundingClientRect()
  tip.value = { show: true, x: e.clientX - rect.left + 12, y: e.clientY - rect.top + 12, dev }
}
function onLeaveDev() {
  tip.value.show = false
}
</script>

<template>
  <div class="rack-view" :class="{ compact }">
    <svg :width="svgW" :height="canvasH" :viewBox="`0 0 ${svgW} ${canvasH}`" class="rack-svg">
      <!-- U 位标签 + 空闲背景 -->
      <template v-for="u in uList" :key="u">
        <rect
          v-if="!occupied.has(u)"
          :x="mainX" :y="blockY(u, 1)" :width="mainW" :height="U_HEIGHT"
          fill="#F5F5F5" stroke="#ddd" stroke-dasharray="3 3" class="free-u"
          @click="emit('mount-u', u)"
        />
        <text v-if="!compact" :x="labelW - 6" :y="blockY(u, 1) + U_HEIGHT / 2 + 4" text-anchor="end" class="u-label">{{ u }}U</text>
      </template>

      <!-- 设备块 -->
      <g
        v-for="d in devices"
        :key="d.id"
        class="device-block"
        @click="emit('select-device', d)"
        @mousemove="onEnterDev($event, d)"
        @mouseleave="onLeaveDev"
      >
        <rect
          :x="mainX + 2" :y="blockY(d.start_u, d.height_u)" :width="mainW - 4"
          :height="deviceBlockHeight(d.height_u)" :fill="deviceColor(d.device_type)"
          rx="3" stroke="#fff" stroke-width="1"
        />
        <text
          v-if="!compact || d.height_u >= 2"
          :x="mainX + mainW / 2" :y="blockY(d.start_u, d.height_u) + d.height_u * U_HEIGHT / 2 + 4"
          text-anchor="middle" class="dev-text"
        >{{ devLabel(d) }}</text>
      </g>
    </svg>

    <div v-if="tip.show && tip.dev" class="dev-tip" :style="{ left: tip.x + 'px', top: tip.y + 'px' }">
      <div><b>{{ tip.dev.resource_code }}</b> · {{ tip.dev.hostname || '—' }}</div>
      <div>{{ tip.dev.brand_name }} / {{ tip.dev.model }}</div>
      <div>类型：{{ tip.dev.device_type }} · U{{ tip.dev.start_u }}-{{ tip.dev.start_u + tip.dev.height_u - 1 }}</div>
      <div>状态：{{ tip.dev.asset_status }}</div>
    </div>
  </div>
</template>

<style scoped>
.rack-view { position: relative; display: inline-block; }
.rack-svg { background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; }
.u-label { font-size: 10px; fill: #666; }
.dev-text { font-size: 9px; fill: #063; font-weight: 600; pointer-events: none; }
.device-block { cursor: pointer; }
.device-block:hover rect { stroke: #1f2d3d; stroke-width: 2; }
.free-u { cursor: pointer; }
.free-u:hover { fill: #e8f7f2; }
.compact .rack-svg { border: none; }
.dev-tip {
  position: absolute; background: rgba(31,45,61,.95); color: #fff; padding: 6px 9px;
  border-radius: 6px; font-size: 11px; line-height: 1.5; pointer-events: none; z-index: 20;
  box-shadow: 0 4px 12px rgba(0,0,0,.3); max-width: 220px;
}
</style>
