import axios from 'axios'

// 统一处理 { code, data, msg } 返回格式
const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

http.interceptors.response.use(
  (resp) => {
    if (resp.config.responseType === 'blob') return resp.data
    const body = resp.data
    if (body && typeof body.code !== 'undefined' && body.code !== 0) {
      return Promise.reject(new Error(body.msg || '请求失败'))
    }
    return body ? body.data : resp.data
  },
  (err) => {
    const msg = err.response?.data?.msg || err.message || '网络错误'
    return Promise.reject(new Error(msg))
  }
)

export const api = {
  // auth
  login: (username, password) => http.post('/auth/login', { username, password }),
  me: () => http.get('/auth/me'),

  // rooms
  listRooms: (params) => http.get('/rooms', { params }),
  getRoom: (id) => http.get(`/rooms/${id}`),
  createRoom: (data) => http.post('/rooms', data),
  updateRoom: (id, data) => http.put(`/rooms/${id}`, data),
  deleteRoom: (id) => http.delete(`/rooms/${id}`),
  roomRacks: (id) => http.get(`/rooms/${id}/racks`),
  roomDeviceTypes: (id) => http.get(`/rooms/${id}/device-types`),

  // racks
  listRacks: (roomId) => http.get('/racks', { params: { room_id: roomId } }),
  getRack: (id) => http.get(`/racks/${id}`),
  createRack: (data) => http.post('/racks', data),
  updateRack: (id, data) => http.put(`/racks/${id}`, data),
  deleteRack: (id) => http.delete(`/racks/${id}`),
  rackDevices: (id) => http.get(`/racks/${id}/devices`),
  rackLayout: (id) => http.get(`/racks/${id}/layout`),

  // devices
  listDevices: (params) => http.get('/devices', { params }),
  getDevice: (id) => http.get(`/devices/${id}`),
  createDevice: (data) => http.post('/devices', data),
  mountDevice: (data) => http.post('/devices/mount', data),
  updateDevice: (id, data) => http.put(`/devices/${id}`, data),
  decommissionDevice: (id) => http.post(`/devices/${id}/decommission`),
  deleteDevice: (id) => http.delete(`/devices/${id}`),

  // import
  importPreview: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/import/preview', fd)
  },
  importCommit: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/import/commit', fd)
  },

  // export
  exportDevices: () => http.get('/devices/export', { responseType: 'blob' }),

  // files
  templateUrl: '/api/files/template',
  sampleUrl: '/api/files/sample',
}

export default api
