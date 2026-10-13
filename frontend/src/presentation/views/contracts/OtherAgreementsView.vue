<template>
  <div class="agreement-section">
    <div class="pdf-content">
      <h2 class="title">اتفاقيات أخرى</h2>

      <p v-if="error" class="form-error" role="alert">{{ error }}</p>

      <table class="form-table">
        <FormRow label="رقم الاتفاقية" required :error="visibleErrors.agreementNumber">
          <input v-model="form.agreementNumber" type="text" placeholder="أدخل رقم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.agreementNumber }" @blur="touch('agreementNumber')" />
        </FormRow>

        <FormRow label="اسم الاتفاقية" required :error="visibleErrors.name">
          <input v-model="form.name" type="text" placeholder="أدخل اسم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.name }" @blur="touch('name')" />
        </FormRow>

        <FormRow label="بداية الاتفاقية" required :error="visibleErrors.startDate">
          <input v-model="form.startDate" type="date" :class="{ 'is-invalid': !!visibleErrors.startDate }"
            @blur="touch('startDate')" />
        </FormRow>

        <FormRow label="نهاية الاتفاقية" required :error="visibleErrors.endDate">
          <input v-model="form.endDate" type="date" :class="{ 'is-invalid': !!visibleErrors.endDate }"
            @blur="touch('endDate')" />
        </FormRow>
      </table>

      <table class="form-table dynamic-rows-table">
        <tbody v-for="(row, index) in form.rows" :key="row.id" class="dynamic-row-group">
          <tr class="dynamic-row-header" dir="rtl">
            <td colspan="2">
              <span class="dynamic-row-number">بند {{ index + 1 }}</span>
              <button type="button" class="remove-row-btn" title="حذف البند" aria-label="حذف البند"
                :disabled="form.rows.length === 1" @click="removeRow(index)">
                ✕ حذف
              </button>
            </td>
          </tr>

          <FormRow label="العنوان" required>
            <input v-model="row.header" type="text" placeholder="أدخل العنوان" />
          </FormRow>

          <FormRow label="المحتوى" required>
            <textarea v-model="row.body" rows="3" placeholder="أدخل المحتوى"></textarea>
          </FormRow>
        </tbody>
      </table>

      <div class="dynamic-rows-footer" dir="rtl">
        <button type="button" class="add-row-btn" @click="addRow">
          ➕ إضافة بند
        </button>
      </div>



      <div class="content-actions-row">
        <button :disabled="saving || !isFormValid" @click="handleSave">
          {{ saving ? 'جارٍ الحفظ...' : 'حفظ الاتفاقية' }}
        </button>

        <label class="checkbox-container">
          <input type="checkbox" id="hide-content-chk" :checked="form.isHidden" @change="toggleContentVisibility" />
          <span>إخفاء المحتوى</span>
        </label>

        <ContractActions class="contract-actions" @print="handlePrint" @upload="handleUpload" />

        <FileChip :file-name="form.fileName" :file-url="form.fileUrl" @remove="handleClearFile" />
        
      </div>

    </div>
  </div>
</template>

<script setup>
import FormRow from '@/presentation/components/FormRow.vue'
import ContractActions from '@/presentation/components/educationalcontent/ContractActions.vue'
import FileChip from '@/presentation/components/educationalcontent/FileChip.vue'
import { useOtherAgreementForm } from '@/presentation/composables/useOtherAgreementForm'
import { useNotifications } from '@/presentation/composables/useNotifications'
const notify = useNotifications()

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
} = useOtherAgreementForm('other-agreements')

let rowIdCounter = 0
const newRow = () => ({
  id: `row-${++rowIdCounter}`,
  header: '',
  body: '',
})

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
    const saved = await save()
    notify.success(response.message)
    console.log('Saved record:', saved)
  } catch (e) {
        notify.error(e.message)
  }
}
</script>