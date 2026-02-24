import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/axios'

interface Item {
  id: number
  name: string
  description: string
}

interface ItemCreate {
  name: string
  description: string
}

export const useItemsStore = defineStore('items', () => {
  const items = ref<Item[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchItems() {
    loading.value = true
    error.value = null
    try {
      const res = await api.get<Item[]>('/items')
      items.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createItem(payload: ItemCreate) {
    loading.value = true
    error.value = null
    try {
      const res = await api.post<Item>('/items', payload)
      items.value.push(res.data)  // Actualiza el state local sin re-fetch
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, fetchItems, createItem }
})