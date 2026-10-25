
<template>
  <main class="app-page" dir="rtl">
    <PageHeader icon="ℹ️" eyebrow="عن النظام" title="نظام إدارة العقود" description="منصة موحدة لإدارة الاتفاقيات والعقود ومتابعة الصلاحيات والتذكيرات." />
    <section class="panel about-copy">
      <h2>منصة عمل موحدة</h2>
      <p>يساعد النظام فرق الجامعة الافتراضية السورية على إدخال الاتفاقيات، تنظيمها، ومتابعة حالتها ضمن صلاحيات واضحة لكل مستخدم.</p>
    </section>
  </main>
</template>

<script setup>
import PageHeader from '@/presentation/components/PageHeader.vue'
</script>

<style scoped>
.about-copy { max-width: 52rem; }
.about-copy h2 { margin-block-end: 0.5rem; }
.about-copy p { margin: 0; color: var(--color-text-muted); line-height: 1.9; }
</style>
