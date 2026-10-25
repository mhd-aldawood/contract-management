<template>
  <div class="payment-section">
    <select :id="inputId" v-model="form.paymentMethod" :aria-describedby="errorId" :aria-invalid="!!errors.paymentMethod"
      :class="{ 'is-invalid': !!errors.paymentMethod }" @blur="$emit('touch', 'paymentMethod')" @change="$emit('touch', 'paymentMethod')">
      <option value="">اختر طريقة الدفع</option>
      <option value="text">نص</option><option value="table">جدول دفعات</option>
    </select>
    <label v-if="form.paymentMethod === 'text'" class="form-field">
      <span>تفاصيل وشروط الدفع</span>
      <textarea v-model="form.paymentText" rows="3" placeholder="أدخل تفاصيل وشروط الدفع" :aria-invalid="!!errors.paymentText"
        :aria-describedby="errors.paymentText ? paymentId + '-text-error' : undefined" :class="{ 'is-invalid': !!errors.paymentText }" @blur="$emit('touch', 'paymentText')"></textarea>
      <small v-if="errors.paymentText" :id="paymentId + '-text-error'" class="field-error">{{ errors.paymentText }}</small>
    </label>
    <div v-if="form.paymentMethod === 'table'" class="payment-schedule">
      <p v-if="errors.paymentSchedule" class="field-error" role="alert">{{ errors.paymentSchedule }}</p>
      <fieldset v-for="(row, i) in form.paymentSchedule" :key="i" class="payment-row">
        <legend>الدفعة {{ i + 1 }}</legend>
        <div class="payment-row__fields">
          <div class="form-field"><label :for="paymentId + '-label-input-' + i">اسم الدفعة</label>
            <input :id="paymentId + '-label-input-' + i" v-model="row.label" type="text" placeholder="مثال: الدفعة الأولى" :class="{ 'is-invalid': !!rowErrors[i]?.label }"
              :aria-invalid="!!rowErrors[i]?.label" :aria-describedby="rowErrors[i]?.label ? paymentId + '-label-' + i : undefined" @blur="$emit('touch', 'paymentSchedule')" />
            <small v-if="rowErrors[i]?.label" :id="paymentId + '-label-' + i" class="field-error">{{ rowErrors[i].label }}</small>
          </div>
          <div class="form-field"><label :for="paymentId + '-amount-input-' + i">المبلغ</label>
            <input :id="paymentId + '-amount-input-' + i" v-model.number="row.amount" type="number" min="0" step="0.01" placeholder="0.00" :class="{ 'is-invalid': !!rowErrors[i]?.amount }"
              :aria-invalid="!!rowErrors[i]?.amount" :aria-describedby="rowErrors[i]?.amount ? paymentId + '-amount-' + i : undefined" @blur="$emit('touch', 'paymentSchedule')" />
            <small v-if="rowErrors[i]?.amount" :id="paymentId + '-amount-' + i" class="field-error">{{ rowErrors[i].amount }}</small>
          </div>
          <div class="form-field"><label :for="paymentId + '-date-input-' + i">تاريخ الاستحقاق</label>
            <input :id="paymentId + '-date-input-' + i" v-model="row.dueDate" type="date" :class="{ 'is-invalid': !!rowErrors[i]?.dueDate }"
              :aria-invalid="!!rowErrors[i]?.dueDate" :aria-describedby="rowErrors[i]?.dueDate ? paymentId + '-date-' + i : undefined" @blur="$emit('touch', 'paymentSchedule')" />
            <small v-if="rowErrors[i]?.dueDate" :id="paymentId + '-date-' + i" class="field-error">{{ rowErrors[i].dueDate }}</small>
          </div>
          <button type="button" class="btn--danger payment-row__remove" :aria-label="'حذف الدفعة ' + (i + 1)" @click="onRemove(i)">حذف</button>
        </div>
      </fieldset>
      <button type="button" class="btn--secondary" @click="onAdd">＋ إضافة دفعة</button>
    </div>
  </div>
</template>

<script setup>
import { useId } from 'vue'

const paymentId = `payment-${useId()}`
const props = defineProps({
  inputId: { type: String, default: undefined },
  errorId: { type: String, default: undefined },
  form: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  rowErrors: { type: Array, default: () => [] },
  addPaymentRow: { type: Function, required: true },
  removePaymentRow: { type: Function, required: true },
})

const emit = defineEmits(['touch'])

function onAdd() {
  props.addPaymentRow()
  emit('touch', 'paymentSchedule')
}
function onRemove(i) {
  props.removePaymentRow(i)
  emit('touch', 'paymentSchedule')
}
</script>
<style scoped>
.payment-section, .payment-schedule { display: grid; gap: 1rem; min-width: 0; }
.payment-row { min-width: 0; padding: 1rem; margin: 0; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-muted-surface); }
.payment-row legend { padding-inline: 0.4rem; font-weight: 700; font-size: 0.9rem; }
.payment-row__fields { display: grid; grid-template-columns: minmax(0, 1.4fr) repeat(2, minmax(0, 1fr)) auto; align-items: start; gap: 0.75rem; }
.payment-row__fields > * { min-width: 0; }
.payment-row__remove { margin-block-start: 1.6rem; }
.field-error { margin: 0; color: var(--color-danger); line-height: 1.6; }
.payment-schedule > button { justify-self: start; }
@container modal-body (max-width: 40rem) {
  .payment-row__fields { grid-template-columns: 1fr; }
  .payment-row__remove { margin-block-start: 0; justify-self: start; }
}
@media (max-width: 640px) {
  .payment-row__fields { grid-template-columns: 1fr; }
  .payment-row__remove { margin-block-start: 0; justify-self: start; }
}
</style>
