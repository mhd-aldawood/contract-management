<template>
  <main class="auth-page" dir="rtl">
    <form class="auth-card" @submit.prevent="submit">
      <h1>تغيير كلمة المرور</h1>
      <p class="auth-card__intro">يجب تغيير كلمة المرور المؤقتة قبل استخدام النظام.</p>

      <PasswordField
        id="current-password"
        v-model="form.currentPassword"
        label="كلمة المرور الحالية"
        autocomplete="current-password"
        required
      />
      <PasswordField
        id="new-password"
        v-model="form.newPassword"
        label="كلمة المرور الجديدة"
        autocomplete="new-password"
        :minlength="8"
        required
      />
      <PasswordField
        id="confirm-new-password"
        v-model="form.newPassword2"
        label="تأكيد كلمة المرور الجديدة"
        autocomplete="new-password"
        :minlength="8"
        required
      />

      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="saving">
        {{ saving ? 'جارٍ الحفظ...' : 'تغيير كلمة المرور' }}
      </button>
    </form>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import container from '@/di/container'
import PasswordField from '@/presentation/components/PasswordField.vue'

const router = useRouter()
const saving = ref(false)
const error = ref('')
const form = reactive({
  currentPassword: '',
  newPassword: '',
  newPassword2: '',
})

async function submit() {
  error.value = ''
  if (form.newPassword !== form.newPassword2) {
    error.value = 'كلمتا المرور الجديدتان غير متطابقتين.'
    return
  }
  saving.value = true
  try {
    await container.authRepository.changePassword({ ...form })
    await router.push('/home')
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.auth-card button[type="submit"] { width: 100%; }
.error { margin: 0; }
</style>
