<template>
  <main class="app-page" dir="rtl">
    <PageHeader icon="📝" eyebrow="العقود" title="اتفاقية مذكرة تفاهم" description="إدارة بيانات ومرفقات مذكرة التفاهم." />
    <section class="panel"><p>سيتم عرض نموذج مذكرة التفاهم هنا.</p></section>
  </main>
</template>

<script setup>
import PageHeader from '@/presentation/components/PageHeader.vue'
</script>

<style scoped>
p { margin: 0; color: var(--color-text-muted); }
</style>
