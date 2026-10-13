<template>
  <div class="payment-section">
    <select v-model="form.paymentMethod" class="table-input" :class="{ 'is-invalid': !!errors.paymentMethod }"
      @blur="$emit('touch', 'paymentMethod')" @change="$emit('touch', 'paymentMethod')">
      <option value="">-- اختر طريقة الدفع --</option>
      <option value="text">نص</option>
      <option value="table">جدول</option>
    </select>
    <p v-if="errors.paymentMethod" class="field-error">⚠ {{ errors.paymentMethod }}</p>

    <div v-if="form.paymentMethod === 'text'" class="payment-text-container">
      <input v-model="form.paymentText" type="text" placeholder="أدخل تفاصيل وشروط الدفع هنا..."
        :class="{ 'is-invalid': !!errors.paymentText }" @blur="$emit('touch', 'paymentText')" />
      <p v-if="errors.paymentText" class="field-error">⚠ {{ errors.paymentText }}</p>

    </div>

    <div v-if="form.paymentMethod === 'table'" class="payment-table-container">
      <p v-if="errors.paymentSchedule" class="field-error">
        ⚠ {{ errors.paymentSchedule }}
      </p>
      <table class="sub-table">
        <thead>
          <tr>
            <th>الدفعة</th>
            <th>المبلغ</th>
            <th>تاريخ الاستحقاق</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in form.paymentSchedule" :key="i">
            <td><input v-model="row.label" type="text" :class="{ 'is-invalid': !!rowErrors[i]?.label }"
                @blur="$emit('touch', 'paymentSchedule')" />
              <p v-if="rowErrors[i]?.label" class="field-error">
                ⚠ {{ rowErrors[i].label }}
              </p>
            </td>
            <td><input v-model.number="row.amount" type="number" placeholder="0.00"
                :class="{ 'is-invalid': !!rowErrors[i]?.amount }" @blur="$emit('touch', 'paymentSchedule')" />
              <p v-if="rowErrors[i]?.amount" class="field-error">
                ⚠ {{ rowErrors[i].amount }}
              </p>
            </td>
            <td>
              <input v-model="row.dueDate" type="date" :class="{ 'is-invalid': !!rowErrors[i]?.dueDate }"
                @blur="$emit('touch', 'paymentSchedule')" />
              <p v-if="rowErrors[i]?.dueDate" class="field-error">
                ⚠ {{ rowErrors[i].dueDate }}
              </p>
            </td>
            <td>
              <button type="button" @click="onRemove(i)">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <button type="button" @click="onAdd">+ إضافة دفعة</button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
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