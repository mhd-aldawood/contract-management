<template>
  <div class="agreement-section">
    <div class="pdf-content">
      <h2 class="title">اتفاقيه مركز نفاذ</h2>

      <!-- optional global summary -->
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p v-if="!canWrite" class="read-only-notice">لديك صلاحية قراءة فقط.</p>

      <fieldset class="permission-fieldset" :disabled="!canWrite">
      <section class="agreement-form-section">
        <h3>بيانات الاتفاقية</h3>
        <div class="agreement-form-grid">
          <FormRow v-slot="{ inputId, errorId }" label="رقم الاتفاقية" required :error="visibleErrors.agreementNumber">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.agreementNumber" type="text" placeholder="أدخل رقم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.agreementNumber }" @blur="touch('agreementNumber')" />
          </FormRow>

          <FormRow v-slot="{ inputId, errorId }" label="اسم الاتفاقية" required :error="visibleErrors.name">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.name" type="text" placeholder="أدخل اسم الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.name }" @blur="touch('name')" />
          </FormRow>

          <FormRow wide v-slot="{ inputId, errorId }" label="اسم الشركة المتعاقد معها" required :error="visibleErrors.companyName">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.companyName" type="text" placeholder="أدخل اسم الشركة"
            :class="{ 'is-invalid': !!visibleErrors.companyName }" @blur="touch('companyName')" />
          </FormRow>

          <FormRow wide v-slot="{ inputId, errorId }" label="موضوع الاتفاقية" required :error="visibleErrors.subject">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.subject" type="text" placeholder="أدخل موضوع الاتفاقية"
            :class="{ 'is-invalid': !!visibleErrors.subject }" @blur="touch('subject')" />

          </FormRow>
        </div>
      </section>

      <section class="agreement-form-section">
        <h3>المدة والتذكير</h3>
        <div class="agreement-form-grid agreement-form-grid--dates">
          <FormRow v-slot="{ inputId, errorId }" label="بداية الاتفاقية" required :error="visibleErrors.startDate">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.startDate" type="date" :class="{ 'is-invalid': !!visibleErrors.startDate }"
            @blur="touch('startDate')" />
          </FormRow>

          <FormRow v-slot="{ inputId, errorId }" label="نهاية الاتفاقية" required :error="visibleErrors.endDate">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.endDate" type="date" :class="{ 'is-invalid': !!visibleErrors.endDate }"
            @blur="touch('endDate')" />
          </FormRow>

          <FormRow v-slot="{ inputId, errorId }" label="تاريخ التذكير">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.reminderDate" type="date" />
          </FormRow>
        </div>
      </section>

      <section class="agreement-form-section">
        <h3>التكلفة وطريقة الدفع</h3>
        <div class="agreement-form-grid">
          <FormRow v-slot="{ inputId, errorId }" label="الكلفة التقديرية" required :error="visibleErrors.estimatedCost">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model.number="form.estimatedCost" type="number" min="0" step="0.01" placeholder="0.00"
            :class="{ 'is-invalid': !!visibleErrors.estimatedCost }" @blur="touch('estimatedCost')" />
          </FormRow>

          <FormRow wide v-slot="{ inputId, errorId }" label="طريقة الدفع" required :error="visibleErrors.paymentMethod">
          <PaymentSection :input-id="inputId" :error-id="errorId" :form="form" :errors="visibleErrors" :row-errors="paymentErrors"
            :add-payment-row="addPaymentRow" :remove-payment-row="removePaymentRow" @touch="touch" />
          </FormRow>
        </div>
      </section>

      <section class="agreement-form-section">
        <h3>الحالة والموازنة</h3>
        <div class="agreement-form-grid">
          <FormRow v-slot="{ inputId, errorId }" label="حالة الاتفاقية" required :error="visibleErrors.status">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model.trim="form.status" type="text" placeholder="مثال: نشط، قيد الانتظار"
            :class="{ 'is-invalid': !!visibleErrors.status }" @blur="touch('status')" />
          </FormRow>

          <FormRow v-slot="{ inputId, errorId }" label="الصرف" :error="visibleErrors.disbursement">
          <input :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model.trim="form.disbursement" type="text" placeholder="تفاصيل الصرف"
            :class="{ 'is-invalid': !!visibleErrors.disbursement }" @blur="touch('disbursement')" />
          </FormRow>

          <FormRow v-slot="{ inputId, errorId }" label="نوع الموازنة" required :error="visibleErrors.budgetType">
          <select :id="inputId" :aria-describedby="errorId" :aria-invalid="!!errorId" v-model="form.budgetType" class="table-input" :class="{ 'is-invalid': !!visibleErrors.budgetType }"
            @blur="touch('budgetType')">
            <option value="current">جاري</option>
            <option value="investment">استثماري</option>
          </select>
          </FormRow>
        </div>
      </section>

      <section class="agreement-form-section">
        <h3>مرفق الاتفاقية</h3>
          <div class="actions-row">
            <ContractActions class="contract-actions" @print="handlePrint" @upload="handleUpload" />
            <FileChip :file-name="form.fileName" :file-url="form.fileUrl" @remove="handleClearFile" />
          </div>
      </section>
      </fieldset>

      <ModalFormActions>
        <button :disabled="!canWrite || saving || !isFormValid" @click="handleSave">
          {{ saving ? 'جارٍ الحفظ...' : 'حفظ الاتفاقية' }}
        </button>
        <label class="checkbox-container">
          <input type="checkbox" id="hide-content-chk" :checked="form.isHidden" :disabled="!canWrite" @change="toggleContentVisibility" />
          <span>إخفاء الاتفاقية عن التخطيط</span>
        </label>
      </ModalFormActions>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import ModalFormActions from '@/presentation/components/ModalFormActions.vue'
import FormRow from '@/presentation/components/FormRow.vue'
import PaymentSection from '@/presentation/components/PaymentSection.vue'
import ContractActions from '@/presentation/components/educationalcontent/ContractActions.vue'
import { useNafathCentersForm } from '@/presentation/composables/useNafathCentersForm'
import FileChip from '@/presentation/components/educationalcontent/FileChip.vue'
import { useNotifications } from '@/presentation/composables/useNotifications'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'

const notify = useNotifications()
const emit = defineEmits(['saved', 'busy'])
const { canWrite } = useFeatureAccess('nafath-centers')
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

watch(saving, value => emit('busy', value), { flush: 'sync' })

async function handleSave() {
  try {
    const response = await save()
    notify.success(response.message || 'تم حفظ الاتفاقية')
    emit('saved', response.data)
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
