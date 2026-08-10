<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const visible = defineModel('visible', { default: false })
const emit = defineEmits(['imported'])

const file = ref(null)
const preview = ref(null)
const committing = ref(false)

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
  preview.value = null
}

async function doPreview() {
  if (!file.value) return ElMessage.warning('请先选择 Excel 文件')
  try {
    preview.value = await api.importPreview(file.value)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function doCommit() {
  if (!preview.value || preview.value.errors.length) return
  committing.value = true
  try {
    const res = await api.importCommit(file.value)
    ElMessage.success(`导入成功：新增 ${res.success_count} 条，更新 ${res.failed_count === 0 ? res.total_rows - res.success_count : 0} 条`)
    visible.value = false
    emit('imported')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    committing.value = false
  }
}

function close() {
  visible.value = false
  file.value = null
  preview.value = null
}
</script>

<template>
  <el-dialog v-model="visible" title="📥 导入设备（Excel）" width="640px" @close="close">
    <el-upload
      drag
      :auto-upload="false"
      :show-file-list="true"
      accept=".xlsx"
      :on-change="onFileChange"
      :on-remove="() => (file = null)"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div>将 Excel 拖到此处，或点击选择（.xlsx）</div>
    </el-upload>

    <div class="actions">
      <el-button @click="doPreview" :disabled="!file">预览校验</el-button>
      <el-button type="primary" :disabled="!preview || preview.errors.length" :loading="committing" @click="doCommit">
        确认导入
      </el-button>
      <el-link type="primary" :href="api.templateUrl" target="_blank" style="margin-left:auto">下载模板</el-link>
      <el-link type="info" :href="api.sampleUrl" target="_blank">下载示例</el-link>
    </div>

    <div v-if="preview" class="result">
      <el-alert
        :title="`共 ${preview.total} 行 · 将新增 ${preview.to_insert} 条 · 将更新 ${preview.to_update} 条`"
        :type="preview.errors.length ? 'warning' : 'success'"
        :closable="false"
        show-icon
      />
      <div v-if="preview.errors.length" class="err-list">
        <div class="err-title">❌ 校验失败（{{ preview.errors.length }} 行，需修正后重新导入）：</div>
        <div v-for="(e, i) in preview.errors.slice(0, 50)" :key="i" class="err-row">{{ e.reason }}</div>
      </div>
      <div v-else class="ok-hint">✅ 校验通过，可点击「确认导入」。</div>
    </div>
  </el-dialog>
</template>

<style scoped>
.actions { display: flex; align-items: center; gap: 10px; margin: 12px 0; }
.result { margin-top: 8px; }
.err-list { max-height: 200px; overflow: auto; background: #fef0f0; border-radius: 6px; padding: 8px 12px; margin-top: 8px; }
.err-title { color: #f56c6c; font-weight: 600; margin-bottom: 4px; }
.err-row { font-size: 12px; color: #a33; line-height: 1.7; }
.ok-hint { color: #67c23a; margin-top: 8px; }
</style>
