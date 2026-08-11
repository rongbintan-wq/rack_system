<script setup>
// 设备类型聚合柱状图（轻量，无第三方图表依赖）
const props = defineProps({ data: { type: Object, default: () => ({ total: 0, by_type: {} }) } })

const palette = {
  交换机: '#50E3C2', 服务器: '#4A90E2', 防火墙: '#F5A623',
  路由器: '#BD10E0', 存储: '#7ED321', KVM: '#9B9B9B', 其他: '#9B9B9B',
}
const maxCount = Math.max(1, ...Object.values(props.data.by_type || {}).map((v) => v.count))
</script>

<template>
  <div class="dt-chart">
    <div v-if="!data.total" class="empty">暂无设备</div>
    <div v-for="(v, type) in data.by_type" :key="type" class="bar-row">
      <span class="label">{{ type }}</span>
      <div class="bar-track">
        <div class="bar-fill" :style="{ width: (v.count / maxCount * 100) + '%', background: palette[type] || '#9B9B9B' }"></div>
      </div>
      <span class="count">{{ v.count }}（运行 {{ v.running }}）</span>
    </div>
  </div>
</template>

<style scoped>
.dt-chart { padding: 4px; }
.bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; }
.label { width: 56px; color: #555; }
.bar-track { flex: 1; background: #f0f0f0; border-radius: 4px; height: 16px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .4s; }
.count { width: 120px; color: #888; font-size: 12px; text-align: right; }
.empty { color: #999; }
</style>
