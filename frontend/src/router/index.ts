import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ItemsView from '../views/ItemsView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/items',
    name: 'Items',
    component: ItemsView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router