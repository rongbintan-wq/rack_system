<script setup>
import { ref, watch } from 'vue'
import { api } from '@/api'
import RackView from './RackView.vue'

const props = defineProps({ racks: { type: Array, default: () => [] } })
const emit = defineEmits(['open-rack', 'edit-rack', 'select-device', 'mount-u'])
const layouts = ref({})

watch(
  () => props.racks,
  async (list) => {
    layouts.value = {}
    await Promise.all(
      list.map(async (r) => {
        try {
          const lay = await api.rackLayout(r.id)
          layouts.value[r.id] = lay
        } catch (e) {
          layouts.value[r.id] = { devices: [], height_u: r.height_u }
        }
      })
    )
  },
  { immediate: true }
)
</script>

<template>
  <div class="rack-grid">
    <div v-for="r in racks" :key="r.id" class="rack-cell" @click="emit('open-rack', r.id)">
      <div class="rack-title">
        <span class="name-wrap">
          <b>{{ r.rack_name }}</b> <span class="code">{{ r.rack_code }}</span>
          <el-tag size="small" :type="r.status === '已满' ? 'danger' : (r.status === '空闲' ? 'info' : 'success')">{{ r.status }}</el-tag>
        </span>
        <el-button text size="small" class="edit-btn" title="编辑机柜" @click.stop="emit('edit-rack', r)">✎</el-button>
      </div>
      <RackView
        :rack="{ height_u: layouts[r.id]?.height_u || r.height_u, rack_name: r.rack_name, rack_code: r.rack_code }"
        :devices="layouts[r.id]?.devices || []"
        compact
        @select-device="emit('select-device', $event)"
        @mount-u="emit('mount-u', { rackCode: r.rack_code, startU: $event })"
      />
      <div class="rack-sub">已用 {{ r.used_u }}/{{ r.height_u }}U · {{ r.device_count }} 台</div>
    </div>
    <div v-if="!racks.length" class="empty">该机房暂无机柜</div>
  </div>
</template>

<style scoped>
.rack-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.rack-cell { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 10px; text-align: center; cursor: pointer; transition: .2s; }
.rack-cell:hover { box-shadow: 0 4px 14px rgba(0,0,0,.12); transform: translateY(-2px); }
.rack-title { font-size: 13px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; gap: 4px; }
.rack-title .name-wrap { display: flex; align-items: center; gap: 4px; min-width: 0; overflow: hidden; }
.rack-title .code { color: #999; font-size: 11px; margin: 0 4px; }
.rack-title .edit-btn { flex-shrink: 0; padding: 2px 4px; color: #909399; }
.rack-title .edit-btn:hover { color: #409EFF; }
.rack-sub { font-size: 11px; color: #888; margin-top: 4px; }
.empty { color: #999; padding: 20px; }
</style>
