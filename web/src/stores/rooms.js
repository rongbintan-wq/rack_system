import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export const useRoomsStore = defineStore('rooms', () => {
  const rooms = ref([])
  const loading = ref(false)

  async function fetchRooms(params) {
    loading.value = true
    try {
      rooms.value = await api.listRooms(params)
    } finally {
      loading.value = false
    }
  }

  async function createRoom(data) {
    const r = await api.createRoom(data)
    await fetchRooms()
    return r
  }

  async function removeRoom(id) {
    await api.deleteRoom(id)
    await fetchRooms()
  }

  return { rooms, loading, fetchRooms, createRoom, removeRoom }
})
