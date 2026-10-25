<template>
  <main class="app-page" dir="rtl">
    <PageHeader icon="⚙️" eyebrow="التفضيلات" title="الإعدادات" description="إدارة تفضيلات العرض والتنبيهات الخاصة بحسابك." />
    <p v-if="!canWrite" class="notice">لديك صلاحية قراءة فقط.</p>
    <section class="panel settings-list">
      <label><span><strong>تفعيل التنبيهات</strong><small>استلام تنبيهات حول العقود والتذكيرات.</small></span><input type="checkbox" :disabled="!canWrite" /></label>
      <label><span><strong>الوضع الداكن</strong><small>استخدام ألوان داكنة عند توفرها.</small></span><input type="checkbox" :disabled="!canWrite" /></label>
      <label><span><strong>التحديث التلقائي</strong><small>تحديث قوائم البيانات تلقائياً.</small></span><input type="checkbox" :disabled="!canWrite" /></label>
    </section>
  </main>
</template>

<script setup>
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
import PageHeader from '@/presentation/components/PageHeader.vue'

const { canWrite } = useFeatureAccess('settings')
</script>

<style scoped>
.settings-list { max-width: 48rem; }
.settings-list label { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid var(--color-border); }
.settings-list label:last-child { border-bottom: 0; }
.settings-list span { display: grid; gap: 0.25rem; }
.settings-list small { color: var(--color-text-muted); line-height: 1.6; }
.settings-list input { width: 1.15rem; height: 1.15rem; }
</style>
