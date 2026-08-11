<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const user = ref(null)
onMounted(async () => {
  try {
    user.value = await api.me()
  } catch (e) {
    // DEV 下无需登录
  }
})
</script>

<template>
  <el-container class="app-root">
    <el-header class="app-header">
      <div class="brand">🗄️ 智能机柜管理系统 <span class="sub">DCIM-Lite</span></div>
      <div class="user">
        <el-tag v-if="user" type="success" size="small">管理员：{{ user.username }}</el-tag>
        <el-tag v-else type="info" size="small">本地调试模式</el-tag>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script>
export default { name: 'App' }
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
.app-root { height: 100vh; }
.app-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #1f2d3d; color: #fff; font-weight: 600;
  border-bottom: 3px solid #50E3C2;
}
.brand .sub { font-size: 12px; opacity: .6; font-weight: 400; margin-left: 6px; }
.app-main { background: #f5f7fa; padding: 16px; overflow: auto; }
.page-title { margin: 0 0 12px; font-size: 18px; }
</style>
