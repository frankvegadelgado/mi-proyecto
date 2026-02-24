<script setup lang="ts">
import { onMounted } from 'vue'
import { useHelloStore } from '../stores/helloStore'

const store = useHelloStore()

onMounted(() => store.fetchHello())
</script>

<template>
  <div>
    <h1>🏠 Home</h1>

    <p v-if="store.loading">Cargando...</p>
    <p v-else-if="store.error" style="color:red">❌ {{ store.error }}</p>
    <div v-else-if="store.data">
      <p>{{ store.data.message }}</p>
      <p>Versión: {{ store.data.version }}</p>
    </div>
  </div>
</template>