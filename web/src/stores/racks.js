import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export const useRacksStore = defineStore('racks', () => {
  const racks = ref([])
  const loading = ref(false)

  async function fetchRacks(roomId) {
    loading.value = true
    try {
      racks.value = await api.listRacks(roomId)
    } finally {
      loading.value = false
    }
  }

  async function createRack(data) {
    const r = await api.createRack(data)
    return r
  }

  async function removeRack(id) {
    await api.deleteRack(id)
  }

  return { racks, loading, fetchRacks, createRack, removeRack }
})
