import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/rooms' },
  {
    path: '/rooms',
    name: 'rooms',
    component: () => import('@/views/RoomsView.vue'),
    meta: { title: '机房管理' },
  },
  {
    path: '/rooms/:id',
    name: 'room-detail',
    component: () => import('@/views/RoomDetailView.vue'),
    meta: { title: '机房详情' },
  },
  {
    path: '/racks/:id',
    name: 'rack-detail',
    component: () => import('@/views/RackDetailView.vue'),
    meta: { title: '机柜详情' },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
