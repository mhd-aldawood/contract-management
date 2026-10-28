<script setup>
import { computed, reactive, ref } from 'vue'
import { apiRequest } from '@/core/api/apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
import { useNotifications } from '@/presentation/composables/useNotifications'
import ModalFormActions from '@/presentation/components/ModalFormActions.vue'
import FileChip from '@/presentation/components/educationalcontent/FileChip.vue'

const emit = defineEmits(['saved', 'busy'])
const { canWrite } = useFeatureAccess('doctoral-contracts')
const notify = useNotifications()
const form = reactive({ contractNumber: '', doctorName: '', tasks: '', doctorRank: '', duration: '', commencementOrder: '', isHidden: false })
const file = ref(null), fileInput = ref(null), saving = ref(false), error = ref('')
const limits = { contractNumber: 100, doctorName: 255, tasks: 10000, doctorRank: 150, duration: 255, commencementOrder: 2000 }
const valid = computed(() => Object.entries(limits).every(([key, max]) => form[key].trim().length > 0 && form[key].length <= max))
const allowed = '.pdf,.png,.jpg,.jpeg,.doc,.docx,.xls,.xlsx,.txt'
function pick(event) {
  error.value = ''
  const picked = event.target.files[0]
  if (!picked) return
  if (!picked.size || picked.size > 19 * 1024 * 1024 || !allowed.split(',').includes('.' + picked.name.split('.').pop().toLowerCase())) {
    error.value = 'اختر وثيقة غير فارغة بصيغة مسموحة وحجم لا يتجاوز 19 ميغابايت.'
    event.target.value = ''
    return
  }
  file.value = picked
}
function clearFile() { file.value = null; if (fileInput.value) fileInput.value.value = '' }
async function save() {
  if (!canWrite.value || !valid.value || saving.value) return
  saving.value = true; emit('busy', true); error.value = ''
  try {
    const body = new FormData()
    for (const [key, value] of Object.entries(form)) body.append(key, typeof value === 'string' ? value.trim() : String(value))
    if (file.value) body.append('file', file.value)
    const response = await apiRequest(API_URLS.doctoralContracts.list, { method: 'POST', body })
    notify.success(response.message)
    emit('saved', response.data)
  } catch (e) { error.value = e.message }
  finally { saving.value = false; emit('busy', false) }
}
</script>
<template>
  <form class="doctoral-form" dir="rtl" @submit.prevent="save">
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <fieldset class="permission-fieldset" :disabled="!canWrite || saving">
      <section class="agreement-form-section">
        <h3>بيانات عقد الدكتوراه</h3>
        <div class="agreement-form-grid">
          <label class="form-field"><span>رقم العقد *</span><input v-model="form.contractNumber" type="text" maxlength="100" placeholder="أدخل رقم العقد" required /></label>
          <label class="form-field"><span>اسم الدكتور *</span><input v-model="form.doctorName" type="text" maxlength="255" placeholder="أدخل اسم الدكتور" required /></label>
          <label class="form-field"><span>رتبة الدكتور *</span><input v-model="form.doctorRank" type="text" maxlength="150" placeholder="مثال: أستاذ مساعد" required /></label>
          <label class="form-field"><span>مدة العقد *</span><input v-model="form.duration" type="text" maxlength="255" placeholder="مثال: سنة دراسية واحدة" required /></label>
          <label class="form-field doctoral-form__wide"><span>المهام *</span><textarea v-model="form.tasks" maxlength="10000" rows="4" placeholder="أدخل مهام الدكتور ضمن العقد" required></textarea></label>
          <label class="form-field doctoral-form__wide"><span>أمر المباشرة *</span><textarea v-model="form.commencementOrder" maxlength="2000" rows="2" placeholder="رقم أمر المباشرة وتفاصيله" required></textarea></label>
        </div>
      </section>
      <section class="agreement-form-section">
        <h3>إرفاق الوثيقة</h3>
        <label class="form-field"><span>وثيقة العقد</span><input ref="fileInput" type="file" :accept="allowed" @change="pick" /><small class="field-hint">PDF أو Word أو صور أو TXT أو Excel، حتى 19 ميغابايت.</small></label>
        <FileChip :file-name="file?.name || ''" @remove="clearFile" />
      </section>
    </fieldset>
    <ModalFormActions>
      <button type="submit" :disabled="!canWrite || saving || !valid" @click.prevent="save">{{ saving ? 'جارٍ الحفظ…' : 'حفظ العقد' }}</button>
      <label class="checkbox-container"><input v-model="form.isHidden" type="checkbox" :disabled="!canWrite || saving" /><span>إخفاء العقد عن التخطيط</span></label>
    </ModalFormActions>
  </form>
</template>
<style scoped>
.doctoral-form { min-width: 0; }
.doctoral-form__wide { grid-column: 1 / -1; }
</style>
