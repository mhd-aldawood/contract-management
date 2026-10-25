<template>
  <div class="not-found">
    <h1 class="code">404</h1>
    <h2 class="title">الصفحة غير موجودة</h2>
    <p class="hint">
      الرابط الذي تحاول الوصول إليه غير موجود أو تم نقله.
    </p>
    <router-link class="home-link" :to="{ name: 'home' }">
      العودة إلى الصفحة الرئيسية
    </router-link>
  </div>
</template>

<script setup>
// Static 404 view — no logic required.
</script>

<style scoped>
.not-found {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem 1rem;
  direction: rtl;
  font-family: inherit;
  color: var(--color-text);
}

.code {
  font-size: 5rem;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-800));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem;
}

.hint {
  font-size: 1rem;
  color: var(--color-text-muted);
  margin: 0 0 1.75rem;
  max-width: 30rem;
  line-height: 1.7;
}

.home-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 1.4rem;
  border-radius: 8px;
  background: var(--color-primary-700);
  color: #fff;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.home-link:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.home-link:active {
  transform: translateY(0);
}
</style>
