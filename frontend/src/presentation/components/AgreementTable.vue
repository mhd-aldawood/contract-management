<script setup>
defineProps({
  agreements:  { type: Array, required: true },
  statusLabel: { type: Function, required: true },
  typeLabel:   { type: Function, required: true },
  formatDate:  { type: Function, required: true },
  formatCost:  { type: Function, required: true },
});
const emit = defineEmits(['open-cost-modal']);
</script>

<template>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>رقم الاتفاقية</th>
          <th>اسم الاتفاقية</th>
          <th>تاريخ البدء</th>
          <th>تاريخ الانتهاء</th>
          <th>تفاصيل العمل</th>
          <th>حالة الاتفاقية</th>
          <th>التكلفة</th>
          <th>تفاصيل التكلفة</th>
          <th>نوع الاتفاقية</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="agreements.length === 0">
          <td colspan="9" class="empty-state">
            لا توجد اتفاقيات تطابق الفلترة المحددة.
          </td>
        </tr>

        <tr v-for="a in agreements" :key="a.number">
          <td>{{ a.number }}</td>
          <td>{{ a.name }}</td>
          <td>{{ formatDate(a.startDate) }}</td>
          <td>{{ formatDate(a.endDate) }}</td>
          <td>{{ a.workDetails }}</td>

          <td>
            <span class="status" :class="`status-${a.status}`">
              {{ statusLabel(a.status) }}
            </span>
          </td>

          <!-- خلية التكلفة -->
          <td>
            <!-- زر "اظهار الجدول" فقط عند showCostTable=true -->
            <button
              v-if="a.showCostTable"
              type="button"
              class="cost-show-table"
              @click="emit('open-cost-modal', a.number)"
            >
              📋 اظهار الجدول
            </button>

            <!-- خلاف ذلك: قيمة التكلفة الثابتة (بدون أي تفاعل) -->
            <span v-else class="cost-value">
              {{ formatCost(a.cost) }}
            </span>
          </td>

          <td>{{ a.costDetails }}</td>

          <td>
            <span class="type" :class="`type-${a.type}`">
              {{ typeLabel(a.type) }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>