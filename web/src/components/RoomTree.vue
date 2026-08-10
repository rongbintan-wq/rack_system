<script setup>
const props = defineProps({ rooms: { type: Array, default: () => [] } })
const emit = defineEmits(['select'])
const active = defineModel('active', { default: null })
</script>

<template>
  <el-menu class="room-tree" :default-active="String(active || '')" @select="(i) => emit('select', Number(i))">
    <el-menu-item index="">
      <el-icon><Grid /></el-icon><span>全部机房</span>
    </el-menu-item>
    <el-menu-item v-for="r in rooms" :key="r.id" :index="String(r.id)">
      <el-icon><OfficeBuilding /></el-icon>
      <span>{{ r.room_name }}</span>
      <span class="cnt">{{ r.total_racks }}</span>
    </el-menu-item>
  </el-menu>
</template>

<style scoped>
.room-tree { border-right: none; }
.cnt { margin-left: auto; color: #999; font-size: 12px; }
</style>
