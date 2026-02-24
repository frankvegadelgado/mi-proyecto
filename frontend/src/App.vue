<script setup lang="ts">
</script>

<template>
  <nav>
    <RouterLink to="/">Home</RouterLink> |
    <RouterLink to="/items">Items</RouterLink>
  </nav>

  <main>
    <RouterView />
  </main>
</template>
