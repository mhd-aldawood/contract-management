<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <h1>Login</h1>
      <form @submit.prevent="handleLogin">
        <input v-model="username" placeholder="Username" required />
        <input v-model="password" type="password" placeholder="Password" required />
        <button type="submit" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="hint">
        Need an account?
        <router-link to="/signup">Sign up</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import container from '@/di/container'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    console.log("loginview ${username.value} ${password.value}")
    await container.loginUseCase.execute({username:username.value,password: password.value})
    router.push('/home')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.auth-card {
  background: #fff;
  padding: 2.5rem;
  border-radius: 12px;
  width: 360px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}
h1 { margin: 0 0 1.5rem; text-align: center; color: #333; }
input {
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 1rem;
}
button {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}
button:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: #e53e3e; text-align: center; margin-top: 1rem; }
.hint { text-align: center; margin-top: 1rem; color: #666; }
.hint a { color: #667eea; text-decoration: none; font-weight: 600; }
</style>