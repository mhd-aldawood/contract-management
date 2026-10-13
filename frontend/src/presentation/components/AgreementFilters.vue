<script setup>
defineProps({
  activeFilters: { type: Object, required: true },
});
const emit = defineEmits(['toggle', 'clear']);

const statusOptions = [
  { value: 'finish',  label: 'منتهية' },
  { value: 'current', label: 'حالية' },
  { value: 'future',  label: 'مستقبلية' },
];

const typeOptions = [
  { value: 'current',    label: 'جاري' },
  { value: 'investment', label: 'استثماري' },
];
</script>

<template>
  <div class="filters">
    <div class="filter-group">
      <div class="filter-label">حالة الاتفاقية</div>
      <div class="filter-buttons">
        <button
          v-for="opt in statusOptions"
          :key="opt.value"
          class="filter-btn"
          :class="{ active: activeFilters.status === opt.value }"
          @click="emit('toggle', 'status', opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div class="filter-group">
      <div class="filter-label">نوع الاتفاقية</div>
      <div class="filter-buttons">
        <button
          v-for="opt in typeOptions"
          :key="opt.value"
          class="filter-btn"
          :class="{ active: activeFilters.type === opt.value }"
          @click="emit('toggle', 'type', opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div class="filter-group">
      <div class="filter-label">&nbsp;</div>
      <div class="filter-buttons">
        <button class="clear-filters-btn" @click="emit('clear')">
          ✕ إلغاء الفلترة
        </button>
      </div>
    </div>
  </div>
</template>