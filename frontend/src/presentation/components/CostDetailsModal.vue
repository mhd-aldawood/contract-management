<script setup>
import { computed } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  agreement: { type: Object, default: null },
  costDetails: { type: Array, default: () => [] },
  formatCost: { type: Function, required: true },
});
const emit = defineEmits(['close']);

const totalPercentage = computed(() =>
  props.costDetails.reduce(
    (sum, item) => sum + parseFloat(String(item.percentage).replace('%', '')),
    0
  )
);

const costDisplay = computed(() =>
  props.agreement?.cost ? props.formatCost(props.agreement.cost) : 'غير محدد'
);
</script>

<template>
  <div
    class="modal-overlay"
    :class="{ active: visible }"
    @click.self="emit('close')"
  >
    <div class="modal-content">
      <div class="modal-header">
        <h2>📊 تفاصيل التكلفة</h2>
        <button class="modal-close" @click="emit('close')">✕</button>
      </div>

      <div v-if="agreement" class="modal-agreement-info">
        <strong>رقم الاتفاقية:</strong> {{ agreement.number }} &nbsp;|&nbsp;
        <strong>اسم الاتفاقية:</strong> {{ agreement.name }} &nbsp;|&nbsp;
        <strong>التكلفة:</strong> {{ costDisplay }}
      </div>

      <table class="modal-table">
        <thead>
          <tr>
            <th>عدد السنوات</th>
            <th>النسبة</th>
            <th>تفاصيل</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in costDetails" :key="i">
            <td>{{ row.years }}</td>
            <td>{{ row.percentage }}</td>
            <td>{{ row.details }}</td>
          </tr>
        </tbody>
      </table>

      <div class="modal-total">المجموع: {{ totalPercentage }}%</div>
    </div>
  </div>
</template>