<script setup>
import { onMounted, reactive, ref } from 'vue'
import { API_URLS } from '@/core/config/apiUrls'
import { apiRequest } from '@/core/api/apiClient'
import PageHeader from '@/presentation/components/PageHeader.vue'
const settings = reactive({ downloadSeconds: 60, accessMinutes: 15, sessionHours: 8, rememberDays: 7, allowRemember: true })
const fields = [
  ['downloadSeconds', 'مدة صلاحية إذن التنزيل بالثواني', 5, 3600],
  ['accessMinutes', 'مدة رمز الوصول بالدقائق', 1, 60],
  ['sessionHours', 'مدة جلسة الدخول بالساعات', 1, 168],
  ['rememberDays', 'مدة تذكرني بالأيام', 1, 90],
]
const loading = ref(true), saving = ref(false), error = ref(''), success = ref('')
async function save() {
  saving.value = true; error.value = ''; success.value = ''
  try {
    Object.assign(settings, (await apiRequest(API_URLS.securitySettings, { method: 'PATCH', body: JSON.stringify(settings) })).data)
    success.value = 'تم حفظ إعدادات الأمان. تقصير المدد يطبق أيضاً على الجلسات والأذونات القائمة.'
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}
onMounted(async () => {
  try { Object.assign(settings, (await apiRequest(API_URLS.securitySettings)).data) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>
<template>
  <div class="page" dir="rtl"><main class="content">
    <PageHeader title="الأمان والجلسات" description="إعدادات مركزية لصلاحية الدخول وتنزيل الملفات. إدارة صلاحيات التنزيل متاحة في صفحة الأدوار والصلاحيات." />
    <p v-if="loading" role="status">جارٍ تحميل الإعدادات…</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-if="success" role="status">{{ success }}</p>
    <form v-if="!loading" class="panel" @submit.prevent="save">
      <div class="modal-form-grid"><label v-for="[key, label, min, max] in fields" :key="key" class="form-field">
        <span>{{ label }}</span><input v-model.number="settings[key]" type="number" :min="min" :max="max" step="1" required :disabled="saving" />
        <small class="field-hint">من {{ min }} إلى {{ max }}</small>
      </label></div>
      <label class="remember-option"><input v-model="settings.allowRemember" type="checkbox" :disabled="saving" /> السماح بخيار تذكرني</label>
      <p class="field-hint">إذن التنزيل يستخدم مرة واحدة، ويستهلك عند بدء تنزيل الملف. لا يوقف انتهاء المدة تنزيلاً بدأ بالفعل.</p>
      <button type="submit" :disabled="saving">{{ saving ? 'جارٍ الحفظ…' : 'حفظ إعدادات الأمان' }}</button>
    </form>
  </main></div>
</template>
<style scoped>.remember-option { display: flex; align-items: center; gap: .6rem; margin-block: 1.5rem; }.remember-option input { width: 1.1rem; height: 1.1rem; }</style>
