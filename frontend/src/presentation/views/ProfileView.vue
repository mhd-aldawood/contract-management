<template>
  <section class="page">
    <h2>👤 Profile</h2>
    <div class="info">
      <p><strong>Username:</strong> {{ user?.username }}</p>
      <p><strong>Email:</strong> {{ user?.email }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import container from '@/di/container'
const user = computed(() => container.authRepository.getCurrentUser())
</script>

<style scoped>
.page { margin-top: 2rem; padding: 2rem; background: #fff; border-radius: 12px; }
h2 { color: #2d3748; margin-top: 0; }
.info p { color: #4a5568; font-size: 1.05rem; }
</style>