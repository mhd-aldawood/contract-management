<script setup>
import BaseModal from './BaseModal.vue'
import { formatContractDate } from '@/presentation/utils/contractDates'
defineProps({ agreement: { type: Object, default: null } })
const emit = defineEmits(['close'])
</script>
<template>
  <BaseModal :model-value="!!agreement" title="جدول تكلفة الاتفاقية" :description="agreement ? `${agreement.name} — ${agreement.agreementNumber}` : ''" size="lg" @update:model-value="emit('close')">
    <template v-if="agreement">
      <div v-if="agreement.costTable?.length" class="table-scroll">
        <table class="planning-cost-table"><thead><tr><th>عدد السنوات</th><th>النسبة</th><th>تفاصيل</th></tr></thead>
          <tbody><tr v-for="(row, index) in agreement.costTable" :key="index"><td>{{ row.years }}</td><td><bdi>{{ row.percentage }}%</bdi></td><td class="cost-details-text">{{ row.details || '—' }}</td></tr></tbody>
        </table>
      </div>
      <template v-else-if="agreement.paymentSchedule?.length">
        <p class="notice">جدول دفعات محفوظ سابقاً بالمبالغ وتواريخ الاستحقاق.</p>
        <div class="table-scroll"><table class="planning-cost-table"><thead><tr><th>اسم الدفعة</th><th>المبلغ</th><th>تاريخ الاستحقاق</th></tr></thead><tbody>
          <tr v-for="(row, index) in agreement.paymentSchedule" :key="index"><td>{{ row.label || '—' }}</td><td>{{ row.amount }}</td><td>{{ formatContractDate(row.dueDate) }}</td></tr>
        </tbody></table></div>
      </template>
      <p v-else class="empty-state">لا توجد صفوف تكلفة محفوظة لهذه الاتفاقية.</p>
    </template>
  </BaseModal>
</template>
<style scoped>
.planning-cost-table { width: 100%; table-layout: fixed; }
.planning-cost-table th, .planning-cost-table td { white-space: normal; overflow-wrap: anywhere; }
.cost-details-text { white-space: pre-wrap !important; }
</style>
