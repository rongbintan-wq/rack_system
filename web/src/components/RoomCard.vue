<script setup>
const props = defineProps({ room: { type: Object, required: true } })
</script>

<template>
  <el-card class="room-card" shadow="hover" @click="$emit('open', room.id)">
    <template #header>
      <div class="rc-head">
        <span class="rc-name">{{ room.room_name }}</span>
        <el-tag size="small" :type="room.status === '在用' ? 'success' : 'warning'">{{ room.status }}</el-tag>
      </div>
    </template>
    <div class="rc-meta">{{ room.region }} · {{ room.province }}{{ room.city }}</div>
    <div class="rc-site">{{ room.site }}</div>
    <el-progress
      :percentage="room.usage_rate || 0"
      :stroke-width="10"
      :color="room.usage_rate > 80 ? '#F5A623' : '#50E3C2'"
    />
    <div class="rc-stats">
      <span>机柜 {{ room.total_racks }}</span>
      <span>占用 {{ room.occupied_racks }}</span>
      <span>空闲 {{ room.free_racks }}</span>
      <span>设备 {{ room.device_count }}</span>
    </div>
  </el-card>
</template>

<style scoped>
.room-card { cursor: pointer; }
.rc-head { display: flex; justify-content: space-between; align-items: center; }
.rc-name { font-weight: 600; }
.rc-meta { color: #666; font-size: 13px; }
.rc-site { color: #999; font-size: 12px; margin: 2px 0 10px; }
.rc-stats { display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #555; }
</style>
