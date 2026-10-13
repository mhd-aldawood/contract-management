<template>
  <div class="agreement-section">
    <div class="pdf-content">
      <h2 class="title">اتفاقيه مركز نفاذ</h2>

      <!-- optional global summary -->
      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <table>
        <FormRow label="رقم الاتفاقية" required :error="visibleErrors.agreementNumber">
          <input v-model="form.agreementNumber" type="text" placeholder="أدخل رقم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.agreementNumber }" @blur="touch('agreementNumber')" />
        </FormRow>

        <FormRow label="اسم الاتفاقية" required :error="visibleErrors.name">
          <input v-model="form.name" type="text" placeholder="أدخل اسم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.name }" @blur="touch('name')" />
        </FormRow>

        <FormRow label="اسم الشركة المتعاقد معها" required :error="visibleErrors.companyName">
          <input v-model="form.companyName" type="text" placeholder="أدخل اسم الشركة"
            :class="{ 'is-invalid': !!visibleErrors.companyName }" @blur="touch('companyName')" />
        </FormRow>

        <FormRow label="موضوع الاتفاقية" required :error="visibleErrors.subject">
          <input v-model="form.subject" type="text" placeholder="أدخل موضوع الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.subject }" @blur="touch('subject')" />
          <div class="actions-row">
            <ContractActions class="contract-actions" @print="handlePrint" @upload="handleUpload" />
            <FileChip :file-name="form.fileName" :file-url="form.fileUrl" @remove="handleClearFile" />
          </div>
        </FormRow>

        <FormRow label="الكلفة التقديرية" required :error="visibleErrors.estimatedCost">
          <input v-model.number="form.estimatedCost" type="number" min="0" step="0.01" placeholder="0.00"
            :class="{ 'is-invalid': !!visibleErrors.estimatedCost }" @blur="touch('estimatedCost')" />
        </FormRow>

        <FormRow label="بداية الاتفاقية" required :error="visibleErrors.startDate">
          <input v-model="form.startDate" type="date" :class="{ 'is-invalid': !!visibleErrors.startDate }"
            @blur="touch('startDate')" />
        </FormRow>

        <FormRow label="نهاية الاتفاقية" required :error="visibleErrors.endDate">
          <input v-model="form.endDate" type="date" :class="{ 'is-invalid': !!visibleErrors.endDate }"
            @blur="touch('endDate')" />
        </FormRow>

        <FormRow label="طريقة الدفع" required :error="visibleErrors.paymentMethod">
          <PaymentSection :form="form" :errors="visibleErrors" :row-errors="paymentErrors"
            :add-payment-row="addPaymentRow" :remove-payment-row="removePaymentRow" @touch="touch" />
        </FormRow>

        <FormRow label="حالة الاتفاقية" required :error="visibleErrors.status">
          <input v-model.trim="form.status" type="text" placeholder="مثال: نشط، قيد الانتظار"
            :class="{ 'is-invalid': !!visibleErrors.status }" @blur="touch('status')" />
        </FormRow>

        <FormRow label="الصرف" :error="visibleErrors.disbursement">
          <input v-model.trim="form.disbursement" type="text" placeholder="تفاصيل الصرف"
            :class="{ 'is-invalid': !!visibleErrors.disbursement }" @blur="touch('disbursement')" />
        </FormRow>

        <FormRow label="نوع الموازنة" required :error="visibleErrors.budgetType">
          <select v-model="form.budgetType" class="table-input" :class="{ 'is-invalid': !!visibleErrors.budgetType }"
            @blur="touch('budgetType')">
            <option value="current">جاري</option>
            <option value="investment">استثماري</option>
          </select>
        </FormRow>
      </table>

      <div class="actions">
        <button :disabled="saving || !isFormValid" @click="handleSave">
          {{ saving ? 'جارٍ الحفظ...' : 'حفظ الاتفاقية' }}
        </button>
        <label class="checkbox-container">
          <input type="checkbox" id="hide-content-chk" :checked="form.isHidden" @change="toggleContentVisibility" />
          <span>إخفاء المحتوى</span>
        </label>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import FormRow from '@/presentation/components/FormRow.vue'
import PaymentSection from '@/presentation/components/PaymentSection.vue'
import ContractActions from '@/presentation/components/educationalcontent/ContractActions.vue'
import { useNafathCentersForm } from '@/presentation/composables/useNafathCentersForm'
import FileChip from '@/presentation/components/educationalcontent/FileChip.vue'
import { useNotifications } from '@/presentation/composables/useNotifications'

const notify = useNotifications()
const {
  form,
  saving,
  error,
  save,
  reset,
  toggleContentVisibility,   // ✅ from composable 
  addPaymentRow,
  removePaymentRow,
  handleFormUpload,
  clearFile,
  visibleErrors,
  paymentErrors,
  isFormValid,
  touch,
} = useNafathCentersForm('nafath-center')

async function handleSave() {
  try {
    const response = await save()
    notify.success(response.message)
  } catch (e) {
    notify.error(e.message)
  }
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

</script>

<style scoped>
.agreement-section {
  padding: 2rem;
}

.title {
  text-align: center;
  margin-bottom: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.5rem;
  border: 1px solid #ddd;
}

th {
  background: #f7fafc;
  text-align: right;
  width: 200px;
}

input,
select,
textarea {
  width: 100%;
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 0.95rem;
}

.actions button {
  padding: 0.6rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: #667eea;
  color: white;
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #e53e3e;
  margin-top: 1rem;
}

.contract-text-area {
  margin-top: 1.5rem;
}

.form-input {
  flex: 1;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  /* ✅ ترتيب عمودي */
  gap: 0.75rem;
  /* ✅ مسافة من الأعلى والأسفل بين العناصر */
  align-items: stretch;
}

.contract-text-area textarea {
  direction: rtl;
  text-align: right;
}

.contract-text-area textarea::placeholder {
  direction: rtl;
  text-align: right;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  direction: rtl;
  /* ✅ ensures right is the start */
  justify-content: flex-start;
  /* ✅ buttons align to the right */
}

.checkbox-container {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #2d3748;
  user-select: none;
  direction: rtl;

  /* ✅ Box styling */
  padding: 0.55rem 1rem;
  border: 1.5px solid #cbd5e0;
  border-radius: 8px;
  background: #ffffff;
  transition: all 0.2s ease;
}

.checkbox-container:hover {
  border-color: #667eea;
  background: #f7fafc;
}

.checkbox-container input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  accent-color: #667eea;
  cursor: pointer;
}

/* ✅ Highlight when checked */
.checkbox-container:has(input:checked) {
  border-color: #667eea;
  background: #edf2ff;
  color: #4c51bf;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  margin-top: 0.5rem;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  font-size: 0.875rem;
  max-width: 100%;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-link {
  color: #2563eb;
  text-decoration: none;
}

.file-remove {
  border: none;
  background: transparent;
  color: #ef4444;
  cursor: pointer;
  font-weight: bold;
}

input.is-invalid:focus,
select.is-invalid:focus,
textarea.is-invalid:focus {
  box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.18);
  border-color: #e53e3e;
}

.actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
