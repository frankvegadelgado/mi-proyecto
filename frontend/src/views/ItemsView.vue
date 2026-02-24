<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useItemsStore } from '../stores/itemsStore'

const store = useItemsStore()

const newName = ref('')
const newDescription = ref('')

onMounted(() => store.fetchItems())

async function handleSubmit() {
  if (!newName.value.trim()) return
  await store.createItem({
    name: newName.value,
    description: newDescription.value,
  })
  newName.value = ''
  newDescription.value = ''
}
</script>

<template>
  <div>
    <h1>📦 Items</h1>

    <!-- Formulario para crear -->
    <form @submit.prevent="handleSubmit">
      <input v-model="newName" placeholder="Nombre" required />
      <input v-model="newDescription" placeholder="Descripción" />
      <button type="submit" :disabled="store.loading">Agregar</button>
    </form>

    <!-- Lista de items -->
    <p v-if="store.loading">Cargando...</p>
    <p v-else-if="store.error" style="color:red">❌ {{ store.error }}</p>
    <ul v-else>
      <li v-for="item in store.items" :key="item.id">
        <strong>{{ item.name }}</strong> — {{ item.description }}
      </li>
    </ul>
  </div>
</template>