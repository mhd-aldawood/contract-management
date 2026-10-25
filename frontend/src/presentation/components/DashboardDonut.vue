<script setup>
import { computed } from 'vue'

const props = defineProps({ items: { type: Array, required: true }, label: { type: String, required: true } })
const total = computed(() => props.items.reduce((sum, item) => sum + item.count, 0))
const number = value => new Intl.NumberFormat('ar-SY').format(value)
const background = computed(() => {
  if (!total.value) return 'var(--color-border)'
  let start = 0
  return `conic-gradient(${props.items.map(item => {
    const end = start + item.count / total.value * 100
    const segment = `${item.color} ${start}% ${end}%`
    start = end
    return segment
  }).join(', ')})`
})
</script>

<template>
  <div class="dashboard-donut">
    <div class="dashboard-donut__ring" :style="{ background }" role="img" :aria-label="`${label}: ${items.map(item => `${item.label} ${item.count}`).join('، ')}`">
      <div><strong>{{ number(total) }}</strong><span>{{ label }}</span></div>
    </div>
    <dl class="dashboard-donut__legend">
      <div v-for="item in items" :key="item.code"><dt><i :style="{ background: item.color }" aria-hidden="true"></i>{{ item.label }}</dt><dd>{{ number(item.count) }}</dd></div>
    </dl>
  </div>
</template>

<style scoped>
.dashboard-donut { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 1.75rem; }
.dashboard-donut__ring { flex: 0 0 11rem; height: 11rem; display: grid; place-items: center; border-radius: 50%; }
.dashboard-donut__ring > div { display: grid; align-content: center; gap: 0.25rem; width: 8rem; height: 8rem; border-radius: 50%; background: var(--color-surface); text-align: center; padding: 0.6rem; }
.dashboard-donut__ring strong { font-size: 2rem; font-variant-numeric: tabular-nums; }
.dashboard-donut__ring span { font-size: 0.8rem; color: var(--color-text-muted); }
.dashboard-donut__legend { flex: 1 1 10rem; margin: 0; display: grid; gap: 1rem; }
.dashboard-donut__legend > div, dt { display: flex; align-items: center; gap: 0.6rem; }
.dashboard-donut__legend > div { justify-content: space-between; }
dt { font-size: 0.9rem; } dd { margin: 0; font-weight: 800; font-variant-numeric: tabular-nums; }
i { width: 0.65rem; height: 0.65rem; border-radius: 50%; flex-shrink: 0; }
</style>
