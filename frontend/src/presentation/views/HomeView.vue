<template>
  <div class="home">
    <AppToolbar />
    <main class="content">
      <h1>Welcome, {{ user?.username }}! 👋</h1>
      <p>Select an item from the toolbar above to navigate.</p>

      <div class="cards">
        <div class="card" @click="$router.push('/home/profile')">
          <div class="card-icon">👤</div>
          <h3>Profile</h3>
          <p>View your profile details</p>
        </div>
        <div class="card" @click="$router.push('/home/settings')">
          <div class="card-icon">⚙️</div>
          <h3>Settings</h3>
          <p>Manage your preferences</p>
        </div>
        <div class="card" @click="$router.push('/home/about')">
          <div class="card-icon">ℹ️</div>
          <h3>About</h3>
          <p>Learn about this app</p>
        </div>
      </div>

      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppToolbar from '@/presentation/components/AppToolbar.vue'
import container from '@/di/container'

const user = computed(() => container.authRepository.getCurrentUser())
</script>

<style scoped>
.home { min-height: 100vh; background: #f7fafc; }
.content { padding: 2rem; max-width: 1000px; margin: 0 auto; }
h1 { color: #2d3748; }
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}
.card {
  background: #fff;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
.card-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.card h3 { margin: 0.5rem 0; color: #2d3748; }
.card p { color: #718096; font-size: 0.9rem; margin: 0; }
</style>