<template>
  <nav class="toolbar">
    <div class="brand" @click="goHome">🏠 MyApp</div>

    <ul class="nav-items">
      <li
        v-for="item in items"
        :key="item.name"
        :class="{
          active: $route.name === item.name,
          'has-dropdown': item.children?.length,
        }"
        @click="navigate(item)"
      >
        <span class="icon">{{ item.icon }}</span>
        {{ item.label }}
        <span v-if="item.children" class="caret">▾</span>

        <!-- القائمة المنسدلة -->
        <ul v-if="item.children?.length" class="dropdown">
          <li
            v-for="child in item.children"
            :key="child.name"
            :class="{ active: $route.name === child.name }"
            @click.stop="navigate(child)"
          >
            <span class="icon">{{ child.icon }}</span>
            {{ child.label }}
          </li>
        </ul>
      </li>
    </ul>

    <button class="logout" @click="handleLogout">Logout</button>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { NAV_ITEMS } from '@/presentation/config/navigation'
import container from '@/di/container'

const router = useRouter()
const items = NAV_ITEMS

function navigate(item) {
  if (item.children) return
  router.push(item.path)
}

function goHome() {
  router.push('/home')
}

async function handleLogout() {
  await container.authRepository.logout()
  router.push('/login')
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #2d3748;
  color: #fff;
  padding: 0 1.5rem;
  height: 60px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
.brand {
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
}
.nav-items {
  list-style: none;
  display: flex;
  gap: 1rem;
  margin: 0;
  padding: 0;
}
.nav-items > li {
  position: relative;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.nav-items > li:hover { background: #4a5568; }
.nav-items > li.active { background: #667eea; }
.icon { font-size: 1rem; }
.caret {
  font-size: 0.7rem;
  opacity: 0.75;
  margin-inline-start: 0.15rem;
}

/* ===== القائمة المنسدلة ===== */
.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: #2d3748;
  list-style: none;
  margin: 0.25rem 0 0;
  padding: 0.5rem 0;
  border-radius: 8px;
  min-width: 260px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s ease;
  z-index: 1000;
}
.nav-items > li.has-dropdown:hover .dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
.dropdown li {
  padding: 0.6rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.15s;
  white-space: nowrap;
}
.dropdown li:hover { background: #4a5568; }
.dropdown li.active { background: #667eea; }

.logout {
  background: #e53e3e;
  border: none;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}
.logout:hover { background: #c53030; }
</style>