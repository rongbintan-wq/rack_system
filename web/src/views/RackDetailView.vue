<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useDevicesStore } from '@/stores/devices'
import RackView from '@/components/RackView.vue'
import ImportDialog from '@/components/ImportDialog.vue'
import DeviceDrawer from '@/components/DeviceDrawer.vue'

const route = useRoute()
const devicesStore = useDevicesStore()
const rack = ref(null)
const devices = ref([])
const layout = ref(null)
const loading = ref(false)

const importVisible = ref(false)
const drawerVisible = ref(false)
const selectedDevice = ref(null)

const mountVisible = ref(false)
const mountSaving = ref(false)
const mountForm = ref({
  resource_code: '', device_type: '交换机', brand_name: '', model: '',
  start_u: 1, height_u: 1, asset_status: '运行中', sn: '', hostname: '',
})

onMounted(load)

async function load() {
  loading.value = true
  const id = route.params.id
  try {
    rack.value = await api.getRack(id)
    devices.value = await api.rackDevices(id)
    layout.value = await api.rackLayout(id)
  } finally {
    loading.value = false
  }
}

function onSelectDevice(d) {
  selectedDevice.value = devices.value.find((x) => x.id === d.id) || d
  drawerVisible.value = true
}

function onMountU(u) {
  mountForm.value = {
    resource_code: '', device_type: '交换机', brand_name: '', model: '',
    start_u: u, height_u: 1, asset_status: '运行中', sn: '', hostname: '',
  }
  mountVisible.value = true
}

async function submitMount() {
  if (!mountForm.value.resource_code) return ElMessage.warning('请填写资源编号')
  mountSaving.value = true
  try {
    await devicesStore.mount({ ...mountForm.value, rack_code: rack.value.rack_code })
    ElMessage.success('上架成功')
    mountVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    mountSaving.value = false
  }
}

async function onImported() {
  await load()
}
async function onDrawerChanged() {
  drawerVisible.value = false
  await load()
}
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/rooms/' + (rack ? rack.room_id : ''))" :content="rack ? rack.rack_name + ' (' + rack.rack_code + ')' : '机柜详情'" />

    <el-card v-if="rack" class="info" shadow="never">
      <el-descriptions :column="5" border>
        <el-descriptions-item label="所属机房">{{ rack.room_name }}</el-descriptions-item>
        <el-descriptions-item label="总U数">{{ rack.height_u }}U</el-descriptions-item>
        <el-descriptions-item label="已用">{{ rack.used_u }}U</el-descriptions-item>
        <el-descriptions-item label="占用率">
          <el-progress :percentage="rack.usage_rate || 0" :color="rack.usage_rate > 80 ? '#F5A623' : '#50E3C2'" style="width:120px" />
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="rack.status === '已满' ? 'danger' : (rack.status === '空闲' ? 'info' : 'success')">{{ rack.status }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="importVisible = true">📥 导入设备</el-button>
      <el-button @click="onMountU(1)">＋ 上架设备</el-button>
      <span class="hint">提示：点击视图中的灰色空闲 U 位可直接上架</span>
    </div>

    <div class="rack-area" v-if="layout">
      <RackView
        :rack="{ height_u: layout.height_u, rack_name: layout.rack_name, rack_code: layout.rack_code }"
        :devices="layout.devices"
        @select-device="onSelectDevice"
        @mount-u="onMountU"
      />
      <div class="legend">
        <div><span class="dot" style="background:#50E3C2"></span>交换机</div>
        <div><span class="dot" style="background:#4A90E2"></span>服务器</div>
        <div><span class="dot" style="background:#F5A623"></span>防火墙</div>
        <div><span class="dot" style="background:#BD10E0"></span>路由器</div>
        <div><span class="dot" style="background:#7ED321"></span>存储</div>
        <div><span class="dot" style="background:#9B9B9B"></span>其他</div>
      </div>
    </div>

    <ImportDialog v-model:visible="importVisible" @imported="onImported" />
    <DeviceDrawer v-model:visible="drawerVisible" :device="selectedDevice" @changed="onDrawerChanged" />

    <el-dialog v-model="mountVisible" title="上架设备" width="460px">
      <el-form :model="mountForm" label-width="90px">
        <el-form-item label="资源编号*" required><el-input v-model="mountForm.resource_code" /></el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="mountForm.device_type">
            <el-option label="交换机" value="交换机" /><el-option label="服务器" value="服务器" />
            <el-option label="防火墙" value="防火墙" /><el-option label="路由器" value="路由器" />
            <el-option label="存储" value="存储" /><el-option label="KVM" value="KVM" /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌"><el-input v-model="mountForm.brand_name" /></el-form-item>
        <el-form-item label="型号"><el-input v-model="mountForm.model" /></el-form-item>
        <el-form-item label="起始U位"><el-input-number v-model="mountForm.start_u" :min="1" :max="rack ? rack.height_u : 42" /></el-form-item>
        <el-form-item label="占用U数"><el-input-number v-model="mountForm.height_u" :min="1" /></el-form-item>
        <el-form-item label="资产状态">
          <el-select v-model="mountForm.asset_status"><el-option label="运行中" value="运行中" /><el-option label="已下架" value="已下架" /><el-option label="维修中" value="维修中" /><el-option label="报废" value="报废" /></el-select>
        </el-form-item>
        <el-form-item label="SN"><el-input v-model="mountForm.sn" /></el-form-item>
        <el-form-item label="主机名"><el-input v-model="mountForm.hostname" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mountVisible = false">取消</el-button>
        <el-button type="primary" :loading="mountSaving" @click="submitMount">上架</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.info { margin: 12px 0; }
.toolbar { margin: 12px 0; display: flex; align-items: center; gap: 10px; }
.hint { color: #999; font-size: 12px; }
.rack-area { display: flex; gap: 24px; align-items: flex-start; background: #fff; border-radius: 8px; padding: 20px; }
.legend { display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: #555; }
.legend .dot { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
</style>
