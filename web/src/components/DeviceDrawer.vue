<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const props = defineProps({ device: { type: Object, default: null } })
const visible = defineModel('visible', { default: false })
const emit = defineEmits(['changed'])

const editing = ref(false)
const form = ref({})
const saving = ref(false)

watch(
  () => props.device,
  (d) => {
    editing.value = false
    if (d) form.value = { ...d }
  }
)

async function save() {
  saving.value = true
  try {
    await api.updateDevice(form.value.id, {
      device_type: form.value.device_type,
      brand_name: form.value.brand_name,
      model: form.value.model,
      rack_code: form.value.rack_code,
      start_u: form.value.start_u,
      height_u: form.value.height_u,
      asset_status: form.value.asset_status,
      sn: form.value.sn,
      hostname: form.value.hostname,
    })
    ElMessage.success('已保存')
    editing.value = false
    emit('changed')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function decommission() {
  await ElMessageBox.confirm('确认将该设备下架（不删除，仅置为已下架）？', '下架确认', { type: 'warning' })
  await api.decommissionDevice(props.device.id)
  ElMessage.success('已下架')
  emit('changed')
}

async function remove() {
  await ElMessageBox.confirm('确认软删除该设备？此操作可在数据中保留痕迹。', '删除确认', { type: 'warning' })
  await api.deleteDevice(props.device.id)
  ElMessage.success('已删除（软删）')
  visible.value = false
  emit('changed')
}
</script>

<template>
  <el-drawer v-model="visible" :title="device ? device.resource_code : ''" size="420px">
    <template v-if="device">
      <el-descriptions v-if="!editing" :column="1" border>
        <el-descriptions-item label="资源ID">{{ device.resource_id }}</el-descriptions-item>
        <el-descriptions-item label="资源编号">{{ device.resource_code }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ device.device_type }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ device.brand_name }}</el-descriptions-item>
        <el-descriptions-item label="型号">{{ device.model }}</el-descriptions-item>
        <el-descriptions-item label="机柜">{{ device.rack_name }} / {{ device.rack_code }}</el-descriptions-item>
        <el-descriptions-item label="U位">U{{ device.start_u }}-{{ device.start_u + device.height_u - 1 }}</el-descriptions-item>
        <el-descriptions-item label="资产状态">
          <el-tag :type="device.asset_status === '运行中' ? 'success' : 'info'">{{ device.asset_status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="SN">{{ device.sn || '—' }}</el-descriptions-item>
        <el-descriptions-item label="主机名">{{ device.hostname || '—' }}</el-descriptions-item>
      </el-descriptions>

      <el-form v-else :model="form" label-width="80px">
        <el-form-item label="设备类型"><el-input v-model="form.device_type" /></el-form-item>
        <el-form-item label="品牌"><el-input v-model="form.brand_name" /></el-form-item>
        <el-form-item label="型号"><el-input v-model="form.model" /></el-form-item>
        <el-form-item label="机柜编号"><el-input v-model="form.rack_code" /></el-form-item>
        <el-form-item label="起始U位"><el-input-number v-model="form.start_u" :min="1" /></el-form-item>
        <el-form-item label="占用U数"><el-input-number v-model="form.height_u" :min="1" /></el-form-item>
        <el-form-item label="资产状态">
          <el-select v-model="form.asset_status">
            <el-option label="运行中" value="运行中" />
            <el-option label="已下架" value="已下架" />
            <el-option label="维修中" value="维修中" />
            <el-option label="报废" value="报废" />
          </el-select>
        </el-form-item>
        <el-form-item label="SN"><el-input v-model="form.sn" /></el-form-item>
        <el-form-item label="主机名"><el-input v-model="form.hostname" /></el-form-item>
      </el-form>

      <div class="drawer-actions">
        <template v-if="!editing">
          <el-button type="primary" @click="editing = true">编辑</el-button>
          <el-button type="warning" @click="decommission">下架</el-button>
          <el-button type="danger" plain @click="remove">删除</el-button>
        </template>
        <template v-else>
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="editing = false">取消</el-button>
        </template>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.drawer-actions { margin-top: 20px; display: flex; gap: 8px; flex-wrap: wrap; }
</style>
