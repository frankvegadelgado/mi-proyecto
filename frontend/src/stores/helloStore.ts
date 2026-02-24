import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/axios'

interface HelloResponse {
  message: string
  version: string
}

export const useHelloStore = defineStore('hello', () => {
  const data = ref<HelloResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHello() {
    loading.value = true
    error.value = null
    try {
      const res = await api.get<HelloResponse>('/hello')
      data.value = res.data
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetchHello }
})