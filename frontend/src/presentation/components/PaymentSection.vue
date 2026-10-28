<script setup>
import { useId } from 'vue'
const paymentId = `payment-${useId()}`
const props = defineProps({
  inputId: { type: String, default: undefined }, errorId: { type: String, default: undefined },
  form: { type: Object, required: true }, errors: { type: Object, default: () => ({}) },
  rowErrors: { type: Array, default: () => [] }, addPaymentRow: Function, removePaymentRow: Function,
})
const emit = defineEmits(['touch'])
function addRow() {
  props.form.costTable ||= []
  props.form.costTable.push({ years: '', percentage: '', details: '' })
  emit('touch', 'costTable')
}
</script>
<template>
  <div class="payment-section">
    <select :id="inputId" v-model="form.paymentMethod" :aria-describedby="errorId" :aria-invalid="!!errors.paymentMethod" @blur="emit('touch', 'paymentMethod')">
      <option value="">اختر نصاً أو جدولاً</option><option value="text">نص</option><option value="table">جدول</option>
    </select>
    <label v-if="form.paymentMethod === 'text'" class="form-field"><span>تفاصيل وشروط الدفع</span>
      <textarea v-model="form.paymentText" rows="3" placeholder="أدخل تفاصيل التكلفة وشروط الدفع" @blur="emit('touch', 'paymentText')"></textarea>
      <small v-if="errors.paymentText" class="field-error">{{ errors.paymentText }}</small>
    </label>
    <div v-if="form.paymentMethod === 'table'" class="payment-schedule">
      <p class="field-hint">أضف عدد السنوات والنسبة والتفاصيل لكل صف. النسبة من 0 إلى 100.</p>
      <fieldset v-for="(row, i) in form.costTable || []" :key="i" class="payment-row">
        <legend>صف التكلفة {{ i + 1 }}</legend>
        <div class="payment-row__fields">
          <label class="form-field"><span>عدد السنوات</span><input v-model.trim="row.years" type="text" maxlength="120" placeholder="مثال: أول 5 سنوات" required /></label>
          <label class="form-field"><span>النسبة</span><input v-model="row.percentage" type="number" min="0" max="100" step="0.01" placeholder="0–100" required /></label>
          <label class="form-field"><span>تفاصيل</span><textarea v-model="row.details" maxlength="2000" rows="2" placeholder="تفاصيل هذا الصف"></textarea></label>
          <button type="button" class="btn--danger payment-row__remove" :aria-label="'حذف صف التكلفة ' + (i + 1)" @click="form.costTable.splice(i, 1)">حذف</button>
        </div>
      </fieldset>
      <button type="button" class="btn--secondary" :disabled="(form.costTable?.length || 0) >= 100" @click="addRow">＋ إضافة صف</button>
    </div>
  </div>
</template>
<style scoped>
.payment-section, .payment-schedule { display: grid; gap: 1rem; min-width: 0; }
.payment-row { min-width: 0; padding: 1rem; margin: 0; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-muted-surface); }
.payment-row legend { padding-inline: .4rem; font-weight: 700; font-size: .9rem; }
.payment-row__fields { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, .7fr) minmax(0, 1.7fr) auto; align-items: start; gap: .75rem; }
.payment-row__fields > * { min-width: 0; }
.payment-row__remove { margin-block-start: 1.6rem; }
.payment-schedule > button { justify-self: start; }
@container modal-body (max-width: 40rem) { .payment-row__fields { grid-template-columns: 1fr; }.payment-row__remove { margin-block-start: 0; justify-self: start; } }
@media (max-width: 640px) { .payment-row__fields { grid-template-columns: 1fr; }.payment-row__remove { margin-block-start: 0; justify-self: start; } }
</style>
