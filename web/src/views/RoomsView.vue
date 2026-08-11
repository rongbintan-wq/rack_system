<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { useRoomsStore } from '@/stores/rooms'
import RoomTree from '@/components/RoomTree.vue'
import RoomCard from '@/components/RoomCard.vue'

const router = useRouter()
const store = useRoomsStore()
const viewMode = ref('table')
const filters = ref({ region: '', city: '', status: '' })
const treeActive = ref(null)

const dialog = ref(false)
const saving = ref(false)
const form = ref({
  room_name: '', building: '', floor: '', total_racks: 0, status: '在用',
  region: '华南', province: '广东', city: '深圳', site: '', owner: '', contact_phone: '', notes: '',
})

onMounted(load)

async function load() {
  await store.fetchRooms(filters.value)
}

function onTreeSelect(id) {
  treeActive.value = id
  // 树形仅用于展示，列表按筛选条件
}

async function openRoom(id) {
  router.push(`/rooms/${id}`)
}

async function submitRoom() {
  if (!form.value.room_name) return ElMessage.warning('请填写机房名称')
  saving.value = true
  try {
    await store.createRoom({ ...form.value })
    ElMessage.success('机房创建成功')
    dialog.value = false
    form.value = { room_name: '', building: '', floor: '', total_racks: 0, status: '在用', region: '华南', province: '广东', city: '深圳', site: '', owner: '', contact_phone: '', notes: '' }
    await load()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function delRoom(row) {
  await ElMessageBox.confirm(`确认软删除机房「${row.room_name}」？其下机柜与设备将一并软删。`, '删除确认', { type: 'warning' })
  await store.removeRoom(row.id)
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="rooms-page">
    <div class="layout">
      <aside class="side">
        <RoomTree :rooms="store.rooms" v-model:active="treeActive" @select="onTreeSelect" />
      </aside>
      <section class="main">
        <div class="toolbar">
          <h3 class="page-title">机房管理</h3>
          <el-select v-model="filters.region" placeholder="区域" clearable style="width:110px" @change="load">
            <el-option label="华南" value="华南" />
          </el-select>
          <el-select v-model="filters.city" placeholder="城市" clearable style="width:110px" @change="load">
            <el-option label="深圳" value="深圳" />
          </el-select>
          <el-select v-model="filters.status" placeholder="状态" clearable style="width:110px" @change="load">
            <el-option label="在用" value="在用" />
            <el-option label="停用" value="停用" />
            <el-option label="预留" value="预留" />
          </el-select>
          <el-radio-group v-model="viewMode" style="margin-left:auto">
            <el-radio-button label="table">表格</el-radio-button>
            <el-radio-button label="card">卡片</el-radio-button>
          </el-radio-group>
          <el-button type="primary" @click="dialog = true">+ 新增机房</el-button>
        </div>

        <el-table v-if="viewMode === 'table'" :data="store.rooms" border stripe @row-dblclick="(r) => openRoom(r.id)">
          <el-table-column prop="room_name" label="机房名称" min-width="140" />
          <el-table-column label="区域/省市" min-width="150">
            <template #default="{ row }">{{ row.region }} {{ row.province }}{{ row.city }}</template>
          </el-table-column>
          <el-table-column prop="total_racks" label="机柜总数" width="100" />
          <el-table-column prop="occupied_racks" label="已占用" width="90" />
          <el-table-column prop="free_racks" label="空闲" width="80" />
          <el-table-column label="占用率" width="160">
            <template #default="{ row }">
              <el-progress :percentage="row.usage_rate || 0" :color="row.usage_rate > 80 ? '#F5A623' : '#50E3C2'" />
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === '在用' ? 'success' : 'warning'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRoom(row.id)">查看</el-button>
              <el-button link type="danger" @click="delRoom(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div v-else class="card-wrap">
          <RoomCard v-for="r in store.rooms" :key="r.id" :room="r" @open="openRoom" />
        </div>
      </section>
    </div>

    <el-dialog v-model="dialog" title="新增机房" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="机房名称*" required><el-input v-model="form.room_name" placeholder="如 开放区01机房" /></el-form-item>
        <el-form-item label="区域"><el-input v-model="form.region" /></el-form-item>
        <el-form-item label="省份/城市"><el-input v-model="form.province" style="width:45%;margin-right:5%" /><el-input v-model="form.city" style="width:50%" /></el-form-item>
        <el-form-item label="楼栋/楼层"><el-input v-model="form.building" style="width:45%;margin-right:5%" /><el-input v-model="form.floor" style="width:50%" /></el-form-item>
        <el-form-item label="场地"><el-input v-model="form.site" /></el-form-item>
        <el-form-item label="机柜总数"><el-input-number v-model="form.total_racks" :min="0" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status"><el-option label="在用" value="在用" /><el-option label="停用" value="停用" /><el-option label="预留" value="预留" /></el-select>
        </el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="form.contact_phone" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitRoom">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.layout { display: flex; gap: 16px; }
.side { width: 200px; background: #fff; border-radius: 8px; padding: 8px; flex-shrink: 0; }
.main { flex: 1; min-width: 0; background: #fff; border-radius: 8px; padding: 14px; }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.page-title { margin: 0; }
.card-wrap { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
</style>
