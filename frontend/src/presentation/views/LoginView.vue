<template>
  <div class="auth-wrapper" dir="rtl">
    <div class="auth-card">
      <h1>تسجيل الدخول</h1>
      <p class="auth-card__intro">نظام إدارة العقود والاتفاقيات</p>
      <form @submit.prevent="handleLogin">
        <label class="form-field">
          <span>اسم المستخدم</span>
          <input v-model="username" autocomplete="username" placeholder="أدخل اسم المستخدم" required />
        </label>
        <PasswordField
          id="login-password"
          v-model="password"
          label="كلمة المرور"
          autocomplete="current-password"
          placeholder="أدخل كلمة المرور"
          required
        />
        <button type="submit" :disabled="loading">
          {{ loading ? 'جارٍ تسجيل الدخول...' : 'تسجيل الدخول' }}
        </button>
      </form>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import container from '@/di/container'
import PasswordField from '@/presentation/components/PasswordField.vue'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const user = await container.loginUseCase.execute({username:username.value,password: password.value})
    router.push(user.mustChangePassword ? '/change-password' : '/home')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-card button[type="submit"] { width: 100%; margin-block-start: 0.25rem; }
.error { margin: 1rem 0 0; }
</style>
