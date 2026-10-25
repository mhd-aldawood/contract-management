<template>
  <main class="app-page" dir="rtl">
    <PageHeader icon="👤" eyebrow="الحساب" title="الحساب الشخصي" description="بيانات الحساب المستخدم حالياً في النظام." />
    <section class="panel profile-card">
      <div class="profile-avatar">{{ user?.username?.charAt(0)?.toUpperCase() }}</div>
      <dl>
        <div><dt>اسم المستخدم</dt><dd>{{ user?.username }}</dd></div>
        <div><dt>البريد الإلكتروني</dt><dd>{{ user?.email || 'غير محدد' }}</dd></div>
        <div><dt>الدور</dt><dd>{{ user?.role?.name || 'غير محدد' }}</dd></div>
      </dl>
    </section>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import container from '@/di/container'
import PageHeader from '@/presentation/components/PageHeader.vue'
const user = computed(() => container.authRepository.getCurrentUser())
</script>

<style scoped>
.profile-card { display: grid; grid-template-columns: auto 1fr; gap: 1.5rem; align-items: start; max-width: 48rem; }
.profile-avatar { display: grid; place-items: center; width: 5rem; height: 5rem; color: #fff; background: var(--color-primary-700); border-radius: var(--radius-lg); font-size: 2rem; font-weight: 800; }
dl { margin: 0; }
dl > div { display: grid; grid-template-columns: 10rem 1fr; gap: 1rem; padding: 0.85rem 0; border-bottom: 1px solid var(--color-border); }
dl > div:last-child { border-bottom: 0; }
dt { color: var(--color-text-muted); font-size: 0.88rem; font-weight: 700; }
dd { margin: 0; color: var(--color-text); font-weight: 700; }
@media (max-width: 560px) { .profile-card { grid-template-columns: 1fr; } dl > div { grid-template-columns: 1fr; gap: 0.25rem; } }
</style>
