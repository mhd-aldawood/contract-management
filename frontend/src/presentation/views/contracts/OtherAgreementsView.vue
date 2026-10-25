<template>
  <form class="other-agreement-form" dir="rtl" @submit.prevent="handleSave">

      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <p v-if="!canWrite" class="read-only-notice">لديك صلاحية قراءة فقط.</p>

      <fieldset class="permission-fieldset" :disabled="!canWrite">
      <section class="agreement-form-section">
      <h3>بيانات الاتفاقية</h3>
      <div class="agreement-form-grid">
        <label class="form-field"><span>رقم الاتفاقية *</span>
          <input v-model="form.agreementNumber" type="text" placeholder="أدخل رقم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.agreementNumber }" @blur="touch('agreementNumber')" />
          <small v-if="visibleErrors.agreementNumber" class="field-error">{{ visibleErrors.agreementNumber }}</small>
        </label>

        <label class="form-field"><span>اسم الاتفاقية *</span>
          <input v-model="form.name" type="text" placeholder="أدخل اسم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.name }" @blur="touch('name')" />
          <small v-if="visibleErrors.name" class="field-error">{{ visibleErrors.name }}</small>
        </label>

      </div>
      </section>
      <section class="agreement-form-section">
      <h3>المدة والتذكير</h3>
      <div class="agreement-form-grid agreement-form-grid--dates">
        <label class="form-field"><span>بداية الاتفاقية *</span>
          <input v-model="form.startDate" type="date" :class="{ 'is-invalid': !!visibleErrors.startDate }"
            @blur="touch('startDate')" />
          <small v-if="visibleErrors.startDate" class="field-error">{{ visibleErrors.startDate }}</small>
        </label>

        <label class="form-field"><span>نهاية الاتفاقية *</span>
          <input v-model="form.endDate" type="date" :min="form.startDate" :class="{ 'is-invalid': !!visibleErrors.endDate }"
            @blur="touch('endDate')" />
          <small v-if="visibleErrors.endDate" class="field-error">{{ visibleErrors.endDate }}</small>
        </label>

        <label class="form-field"><span>تاريخ التذكير</span>
          <input v-model="form.reminderDate" type="date" />
        </label>
      </div>
      </section>

      <section class="agreement-form-section agreement-clauses">
        <div class="panel-heading"><h3>بنود الاتفاقية</h3><button type="button" class="btn--secondary btn--sm" @click="addRow">إضافة بند</button></div>
        <section v-for="(row, index) in form.rows" :key="row.id" class="agreement-clause">
          <header class="panel-heading">
              <span class="dynamic-row-number">بند {{ index + 1 }}</span>
              <button type="button" class="remove-row-btn" title="حذف البند" aria-label="حذف البند"
                :disabled="form.rows.length === 1" @click="removeRow(index)">
                ✕ حذف
              </button>
          </header>

          <label class="form-field"><span>العنوان</span>
            <input v-model="row.header" type="text" placeholder="أدخل العنوان" />
          </label>

          <label class="form-field"><span>المحتوى</span>
            <textarea v-model="row.body" rows="3" placeholder="أدخل المحتوى"></textarea>
          </label>
        </section>
      </section>
      <section class="agreement-form-section">
      <h3>مرفق الاتفاقية</h3>
      <div class="content-actions-row">
        <ContractActions class="contract-actions" :upload-disabled="!canWrite" @print="handlePrint" @upload="handleUpload" />

        <FileChip :file-name="form.fileName" :file-url="form.fileUrl" :removable="canWrite" @remove="handleClearFile" />

      </div>
      </section>
      </fieldset>

      <ModalFormActions>
        <button type="button" :disabled="!canWrite || saving || !isFormValid" @click="handleSave">
          {{ saving ? 'جارٍ الحفظ...' : 'حفظ الاتفاقية' }}
        </button>
        <label class="checkbox-container">
          <input type="checkbox" :checked="form.isHidden" :disabled="!canWrite" @change="toggleContentVisibility" />
          <span>إخفاء الاتفاقية عن التخطيط</span>
        </label>
      </ModalFormActions>

  </form>
</template>

<script setup>
import { watch } from 'vue'
import ModalFormActions from '@/presentation/components/ModalFormActions.vue'
import ContractActions from '@/presentation/components/educationalcontent/ContractActions.vue'
import FileChip from '@/presentation/components/educationalcontent/FileChip.vue'
import { useOtherAgreementForm } from '@/presentation/composables/useOtherAgreementForm'
import { useNotifications } from '@/presentation/composables/useNotifications'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
const notify = useNotifications()
const props = defineProps({ agreementType: { type: String, default: 'other-agreements' } })
const emit = defineEmits(['saved', 'busy'])
const { canWrite } = useFeatureAccess(props.agreementType)

const {
  form,
  saving,
  error,
  save,
  reset,
  toggleContentVisibility,
  handleFormUpload,
  clearFile,
  touch,
  visibleErrors,
  isFormValid,
} = useOtherAgreementForm(props.agreementType)

watch(saving, value => emit('busy', value), { flush: 'sync' })

let rowIdCounter = 0
const newRow = () => ({
  id: `row-${++rowIdCounter}`,
  header: '',
  body: '',
})
addRow()

function addRow() {
  form.rows.push(newRow())
}

function removeRow(index) {
  if (form.rows.length <= 1) return
  form.rows.splice(index, 1)
}

function handlePrint() {
  window.print()
}

function handleClearFile() {
  clearFile()
}

function handleUpload(payload) {
  handleFormUpload(payload)
}

async function handleSave() {
  try {
    const response = await save()
    notify.success(response.message || 'تم حفظ الاتفاقية')
    emit('saved', response.data)
  } catch (e) {
        notify.error(e.message)
  }
}
</script>

<style scoped>
.other-agreement-form { display: grid; gap: 1rem; }
.agreement-clauses { margin-block-start: 1.5rem; }
.agreement-clauses h3 { margin: 0; }
.agreement-clause { display: grid; gap: 1rem; padding: 1rem; margin-block-end: 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-muted-surface); }
.agreement-clause .panel-heading { margin: 0; }
.content-actions-row { display: flex; align-items: center; flex-wrap: wrap; gap: 0.75rem; }
.field-error { color: var(--color-danger); }
.permission-fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
.read-only-notice { color: #744210; background: #fffff0; padding: 0.75rem; border-radius: 8px; }
</style>
