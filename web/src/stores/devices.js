import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref([])

  async function fetchByRack(rackId) {
    devices.value = await api.rackDevices(rackId)
    return devices.value
  }

  async function mount(data) {
    const r = await api.mountDevice(data)
    return r
  }

  async function update(id, data) {
    return await api.updateDevice(id, data)
  }

  async function decommission(id) {
    return await api.decommissionDevice(id)
  }

  async function remove(id) {
    return await api.deleteDevice(id)
  }

  return { devices, fetchByRack, mount, update, decommission, remove }
})
