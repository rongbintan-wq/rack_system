<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useRacksStore } from '@/stores/racks'
import RackGrid from '@/components/RackGrid.vue'
import DeviceTypeChart from '@/components/DeviceTypeChart.vue'

const route = useRoute()
const router = useRouter()
const racksStore = useRacksStore()
const room = ref(null)
const racks = ref([])
const dtypes = ref({ total: 0, by_type: {} })
const loading = ref(false)

const rackDialog = ref(false)
const saving = ref(false)
const rackForm = ref({ rack_name: '', rack_code: '', height_u: 42, power_type: '双路市电', status: '空闲', location_note: '', notes: '' })

onMounted(load)

async function load() {
  loading.value = true
  const id = route.params.id
  try {
    room.value = await api.getRoom(id)
    racks.value = await api.roomRacks(id)
    dtypes.value = await api.roomDeviceTypes(id)
  } finally {
    loading.value = false
  }
}

function openRack(id) {
  router.push(`/racks/${id}`)
}

async function submitRack() {
  if (!rackForm.value.rack_name || !rackForm.value.rack_code) return ElMessage.warning('请填写机柜名称与编号')
  saving.value = true
  try {
    await racksStore.createRack({ ...rackForm.value, room_id: Number(route.params.id) })
    ElMessage.success('机柜创建成功')
    rackDialog.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/rooms')" :content="room?.room_name || '机房详情'" />

    <el-card v-if="room" class="info" shadow="never">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="区域">{{ room.region }} {{ room.province }}{{ room.city }}</el-descriptions-item>
        <el-descriptions-item label="场地">{{ room.site }}</el-descriptions-item>
        <el-descriptions-item label="负责人">{{ room.owner || '—' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ room.contact_phone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="机柜总数">{{ room.total_racks }}</el-descriptions-item>
        <el-descriptions-item label="已占用">{{ room.occupied_racks }}</el-descriptions-item>
        <el-descriptions-item label="空闲">{{ room.free_racks }}</el-descriptions-item>
        <el-descriptions-item label="设备数">{{ room.device_count }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <div class="section-head">
      <h3>机柜矩阵</h3>
      <el-button type="primary" size="small" @click="rackDialog = true">+ 新增机柜</el-button>
    </div>
    <RackGrid :racks="racks" @open-rack="openRack" />

    <div class="section-head"><h3>设备类型分布</h3></div>
    <el-card shadow="never"><DeviceTypeChart :data="dtypes" /></el-card>

    <el-dialog v-model="rackDialog" title="新增机柜" width="460px">
      <el-form :model="rackForm" label-width="90px">
        <el-form-item label="机柜名称*" required><el-input v-model="rackForm.rack_name" placeholder="如 A01" /></el-form-item>
        <el-form-item label="机柜编号*" required><el-input v-model="rackForm.rack_code" placeholder="如 RACK-A01-01" /></el-form-item>
        <el-form-item label="总U数">
          <el-select v-model="rackForm.height_u"><el-option :value="42" /><el-option :value="45" /><el-option :value="47" /><el-option :value="48" /></el-select>
        </el-form-item>
        <el-form-item label="电源类型"><el-input v-model="rackForm.power_type" /></el-form-item>
        <el-form-item label="位置备注"><el-input v-model="rackForm.location_note" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rackDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitRack">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.info { margin: 12px 0; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin: 18px 0 10px; }
.section-head h3 { margin: 0; }
</style>
