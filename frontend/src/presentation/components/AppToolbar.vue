<template>
  <header class="mobile-header">
    <button type="button" class="mobile-menu-button" aria-label="فتح القائمة" @click="mobileOpen = true">☰</button>
    <button type="button" class="mobile-brand" @click="goHome">
      <strong>إدارة العقود</strong>
    </button>
  </header>

  <button
    v-if="mobileOpen"
    type="button"
    class="sidebar-overlay"
    aria-label="إغلاق القائمة"
    @click="mobileOpen = false"
  ></button>

  <aside class="sidebar" :class="{ 'sidebar--open': mobileOpen }" aria-label="التنقل الرئيسي">
    <header class="sidebar-header">
      <button type="button" class="brand" @click="goHome">
        <span class="brand-copy">
          <strong>إدارة العقود</strong>
          <small>الجامعة الافتراضية السورية</small>
        </span>
      </button>
      <button type="button" class="sidebar-close" aria-label="إغلاق القائمة" @click="mobileOpen = false">✕</button>
    </header>

    <nav class="sidebar-nav">
      <section v-for="group in groups" :key="group.key" class="nav-group">
        <h2>{{ group.label }}</h2>
        <ul>
          <li v-for="item in group.items" :key="item.name">
            <button
              type="button"
              class="nav-link"
              :class="{ active: route.name === item.name }"
              :aria-current="route.name === item.name ? 'page' : undefined"
              @click="navigate(item)"
            >
              <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </button>
          </li>
        </ul>
      </section>
    </nav>

    <footer class="sidebar-footer">
      <button type="button" class="account-card" @click="navigate({ path: '/profile' })">
        <span class="account-avatar">{{ userInitial }}</span>
        <span class="account-copy">
          <strong>{{ currentUser?.username }}</strong>
          <small>{{ currentUser?.role?.name || 'مستخدم النظام' }}</small>
        </span>
      </button>
      <button type="button" class="logout" @click="handleLogout">
        <span aria-hidden="true">⇥</span>
        تسجيل الخروج
      </button>
    </footer>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NAV_GROUPS } from '@/presentation/config/navigation'
import container from '@/di/container'

const router = useRouter()
const route = useRoute()
const mobileOpen = ref(false)
const currentUser = computed(() => container.authRepository.getCurrentUser())
const userInitial = computed(() => currentUser.value?.username?.charAt(0)?.toUpperCase() || 'م')
const groups = computed(() => NAV_GROUPS
  .filter((group) => !group.adminOnly || container.authRepository.isAdmin())
  .map((group) => ({
    ...group,
    items: group.items.filter((item) => {
      if (item.hideForAdmin && container.authRepository.isAdmin()) return false
      if (item.adminOnly && !container.authRepository.isAdmin()) return false
      return !item.feature || container.authRepository.hasPermission(item.feature, 'read')
    }),
  }))
  .filter((group) => group.items.length > 0))

function navigate(item) {
  mobileOpen.value = false
  router.push(item.path)
}

function goHome() {
  router.push('/home')
}

async function handleLogout() {
  try { await container.authRepository.logout() }
  finally { router.push('/login') }
}
</script>

<style scoped>
.toolbar {
  position: fixed;
  inset: 0 0 auto;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  height: var(--toolbar-height);
  padding: 0 1.25rem;
  background: var(--color-navy-950);
  color: #fff;
  border-bottom: 1px solid rgb(255 255 255 / 10%);
  box-shadow: 0 8px 24px rgb(15 23 42 / 14%);
}
.brand {
  display: flex !important;
  align-items: center;
  gap: 0.65rem;
  min-width: max-content;
  padding: 0 !important;
  color: #fff !important;
  background: transparent !important;
  border: 0 !important;
  text-align: right;
}
.brand-copy { display: grid; gap: 0.05rem; }
.brand-copy strong { font-size: 0.95rem; }
.brand-copy small { color: #aab9c5; font-size: 0.68rem; }
.nav-items {
  list-style: none;
  display: flex;
  align-items: center;
  gap: 0.2rem;
  margin: 0;
  padding: 0;
}
.nav-items > li { position: relative; }
.nav-link,
.dropdown-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.5rem !important;
  padding: 0.55rem 0.7rem !important;
  color: #dbe5ea !important;
  background: transparent !important;
  border: 0 !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.82rem;
  white-space: nowrap;
}
.nav-link:hover, .nav-items > li.active > .nav-link { color: #fff !important; background: rgb(255 255 255 / 10%) !important; }
.nav-items > li.active > .nav-link { box-shadow: inset 0 -2px var(--color-primary-500); }
.icon { font-size: 1rem; }
.caret { margin-inline-start: 0.15rem; color: #93a6b3; }
.dropdown {
  position: absolute;
  inset-block-start: calc(100% + 0.55rem);
  inset-inline-start: 0;
  list-style: none;
  min-width: 18rem;
  margin: 0;
  padding: 0.45rem;
  background: var(--color-navy-900);
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-0.4rem);
  transition: 150ms ease;
}
.nav-items > li.has-dropdown:hover .dropdown,
.nav-items > li.dropdown-open .dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
.dropdown-link { width: 100%; }
.dropdown-link:hover, .dropdown-link.active { color: #fff !important; background: rgb(255 255 255 / 10%) !important; }
.account-actions { display: flex; align-items: center; gap: 0.65rem; min-width: max-content; }
.account-name { color: #b6c5ce; font-size: 0.78rem; }
.logout { min-height: 2.2rem !important; padding: 0.45rem 0.7rem !important; color: #fecaca !important; background: rgb(185 28 28 / 18%) !important; border-color: rgb(248 113 113 / 30%) !important; font-size: 0.78rem; }
.logout:hover { background: rgb(185 28 28 / 30%) !important; }
.menu-toggle { display: none !important; color: #fff !important; background: transparent !important; border-color: rgb(255 255 255 / 18%) !important; }

@media (max-width: 1100px) {
  .brand-copy small, .account-name { display: none; }
  .nav-link { padding-inline: 0.5rem !important; }
}

@media (max-width: 860px) {
  .menu-toggle { display: inline-flex !important; margin-inline-start: auto; }
  .nav-items {
    position: fixed;
    inset: var(--toolbar-height) 0 auto;
    display: none;
    align-items: stretch;
    max-height: calc(100vh - var(--toolbar-height));
    padding: 0.75rem;
    overflow-y: auto;
    background: var(--color-navy-950);
    border-top: 1px solid rgb(255 255 255 / 10%);
    box-shadow: var(--shadow-lg);
  }
  .nav-items--open { display: grid; }
  .nav-link { width: 100%; justify-content: flex-start; }
  .dropdown { position: static; display: none; min-width: 0; margin: 0.25rem 1rem 0; opacity: 1; visibility: visible; transform: none; box-shadow: none; }
  .dropdown-open .dropdown { display: block; }
  .account-actions { margin-inline-start: 0; }
}

@media (max-width: 480px) {
  .toolbar { padding-inline: 0.75rem; }
  .brand-copy strong { font-size: 0.82rem; }
  .logout { font-size: 0; }
  .logout::before { content: 'خروج'; font-size: 0.75rem; }
}

/* CRM-style application sidebar */
.sidebar {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  z-index: 2100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100dvh;
  width: var(--sidebar-width);
  color: #fff;
  background: var(--color-navy-950);
  border-inline-end: 1px solid rgb(255 255 255 / 8%);
  box-shadow: 0 0 28px rgb(15 23 42 / 14%);
}
.sidebar-header { display: flex; align-items: center; min-height: 5rem; padding: 1rem; border-bottom: 1px solid rgb(255 255 255 / 9%); }
.sidebar-header .brand { flex: 1; }
.sidebar-header .brand-copy strong { font-size: 1rem; }
.sidebar-header .brand-copy small { display: block; }
.sidebar-close { display: none !important; color: #dbe5ea !important; background: transparent !important; border-color: rgb(255 255 255 / 15%) !important; }
.sidebar-nav { flex: 1; min-height: 0; padding: 0.8rem; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; scrollbar-width: none; }
.sidebar-nav::-webkit-scrollbar { display: none; }
.sidebar-header, .sidebar-footer { flex-shrink: 0; }
.nav-group { margin-block-end: 1rem; }
.nav-group h2 { margin: 0 0 0.35rem; padding: 0 0.65rem; color: #7f96a5; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.04em; }
.nav-group ul { display: grid; gap: 0.18rem; padding: 0; margin: 0; list-style: none; }
.sidebar .nav-link {
  display: flex !important;
  align-items: center;
  justify-content: flex-start !important;
  gap: 0.75rem !important;
  width: 100%;
  min-height: 2.75rem !important;
  padding: 0.65rem 0.75rem !important;
  color: #c9d6de !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.86rem;
  text-align: right;
}
.sidebar .nav-link:hover { color: #fff !important; background: rgb(255 255 255 / 7%) !important; }
.sidebar .nav-link.active { color: #fff !important; background: rgb(20 184 166 / 18%) !important; border-color: rgb(45 212 191 / 20%) !important; box-shadow: inset -3px 0 var(--color-primary-500); }
.nav-icon { display: grid; place-items: center; width: 1.65rem; height: 1.65rem; color: #8facb8; font-size: 1.05rem; }
.nav-link.active .nav-icon { color: #5eead4; }
.sidebar-footer { display: grid; gap: 0.65rem; padding: 0.8rem; border-top: 1px solid rgb(255 255 255 / 9%); }
.account-card { display: grid !important; grid-template-columns: auto 1fr; justify-content: initial !important; gap: 0.7rem !important; width: 100%; padding: 0.65rem !important; color: #fff !important; background: rgb(255 255 255 / 5%) !important; border-color: rgb(255 255 255 / 8%) !important; text-align: right; }
.account-avatar { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; background: var(--color-primary-700); border-radius: 50%; font-weight: 800; }
.account-copy { display: grid; align-content: center; gap: 0.1rem; min-width: 0; }
.account-copy strong, .account-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-copy small { color: #8fa5b2; font-size: 0.7rem; }
.sidebar-footer .logout { width: 100%; justify-content: flex-start !important; }
.mobile-header { display: none; }
.sidebar-overlay { display: none !important; }

@media (max-width: 900px) {
  .mobile-header {
    position: fixed;
    inset: 0 0 auto;
    z-index: 2050;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: var(--mobile-header-height);
    padding: 0 0.75rem;
    color: #fff;
    background: var(--color-navy-950);
    box-shadow: var(--shadow-md);
  }
  .mobile-menu-button, .mobile-brand { color: #fff !important; background: transparent !important; border-color: rgb(255 255 255 / 14%) !important; }
  .mobile-brand { gap: 0.55rem !important; border: 0 !important; }
  .sidebar { width: min(var(--sidebar-width), calc(100vw - 2.5rem)); transform: translateX(105%); transition: transform 180ms ease; }
  .sidebar--open { transform: translateX(0); }
  .sidebar-close { display: inline-flex !important; }
  .sidebar-overlay { position: fixed; inset: 0; z-index: 2075; display: block !important; width: 100%; height: 100%; padding: 0 !important; background: rgb(15 23 42 / 55%) !important; border: 0 !important; border-radius: 0 !important; backdrop-filter: blur(2px); }
}
</style>
