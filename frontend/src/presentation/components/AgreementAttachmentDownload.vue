<script setup>
import { computed, ref } from 'vue'
import container from '@/di/container'
import { downloadDocument } from '@/core/api/fileDownloads'
const props = defineProps({ agreement: { type: Object, required: true }, scope: { type: String, default: 'agreement' } })
const label = computed(() => props.agreement.feature === 'doctoral-contracts' ? 'تنزيل الوثيقة' : 'تنزيل مرفق الاتفاقية')
const busy = ref(false)
const error = ref('')
const allowed = computed(() => container.authRepository.hasPermission(props.scope === 'agreement' ? props.agreement.feature : props.scope, 'download'))
async function download() {
  if (busy.value || !allowed.value) return
  busy.value = true; error.value = ''
  try { await downloadDocument({ ...props.agreement, scope: props.scope, fileName: props.agreement.fileName || 'document' }) }
  catch (e) { error.value = e.message }
  finally { busy.value = false }
}
</script>
<template>
  <div v-if="agreement.hasFile" class="attachment-download">
    <button type="button" class="btn--secondary" :disabled="busy || !allowed" @click="download">{{ busy ? 'جارٍ التنزيل…' : label }}</button>
    <small v-if="!allowed">لا تملك صلاحية تنزيل الملفات لهذه الصفحة.</small>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>
<style scoped>.attachment-download { display: grid; justify-items: start; gap: .5rem; margin-block: 1rem; }</style>
