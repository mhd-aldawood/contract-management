<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <h1>Sign Up</h1>
      <form @submit.prevent="handleSignup">
        <input v-model="username" placeholder="Username" required />
        <input v-model="email" type="email" placeholder="Email" required />

        <div class="password-field">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Password"
            required
          />
          <button
            type="button"
            class="toggle-btn"
            @click="showPassword = !showPassword"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
          >
            <!-- eye / eye-off -->
            <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
              <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
              <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>
        </div>

        <div class="password-field">
          <input
            v-model="password2"
            :type="showPassword2 ? 'text' : 'password'"
            placeholder="Confirm Password"
            required
          />
          <button
            type="button"
            class="toggle-btn"
            @click="showPassword2 = !showPassword2"
            :aria-label="showPassword2 ? 'Hide password' : 'Show password'"
          >
            <svg v-if="!showPassword2" xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
              <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
              <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? 'Creating...' : 'Create Account' }}
        </button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="hint">
        Already have an account?
        <router-link to="/login">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import  container  from '@/di/container'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const password2 = ref('')
const showPassword = ref(false)
const showPassword2 = ref(false)
const error = ref('')
const loading = ref(false)

async function handleSignup() {
  error.value = ''

  if (password.value !== password2.value) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true
  try {
    await container.signupUseCase.execute({
      username: username.value,
      email: email.value,
      password: password.value,
      password2: password2.value,
    })
    router.push('/login')
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

/* wrapper for password inputs so the icon can sit inside */
.password-field {
  position: relative;
}
.password-field input {
  padding-right: 2.75rem;   /* room for the icon */
  margin-bottom: 1rem;
}
.toggle-btn {
  position: absolute;
  top: 50%;
  right: 0.5rem;
  transform: translateY(-50%) translateY(-0.5rem); /* offset for the input's bottom margin */
  width: auto;
  padding: 0.25rem;
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.toggle-btn:hover { color: #667eea; }

button[type="submit"] {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}
button[type="submit"]:disabled { opacity: 0.6; cursor: not-allowed; }

.error { color: #e53e3e; text-align: center; margin-top: 1rem; }
.hint { text-align: center; margin-top: 1rem; color: #666; }
.hint a { color: #667eea; text-decoration: none; font-weight: 600; }
</style>