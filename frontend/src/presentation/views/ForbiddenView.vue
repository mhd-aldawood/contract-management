<template>
  <main class="forbidden" dir="rtl">
    <div class="card">
      <div class="icon">🔒</div>
      <h1>غير مصرح لك</h1>
      <p>لا تملك صلاحية الوصول إلى هذه الصفحة.</p>
      <button type="button" @click="$router.push('/home')">العودة إلى الرئيسية</button>
    </div>
  </main>
</template>

<style scoped>
.forbidden {
  min-height: calc(100vh - var(--toolbar-height));
  display: grid;
  place-items: center;
  background: var(--color-canvas);
}
.card {
  width: min(420px, calc(100% - 2rem));
  padding: 2.5rem;
  text-align: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}
.icon { font-size: 3rem; }
p { color: var(--color-text-muted); }
</style>
