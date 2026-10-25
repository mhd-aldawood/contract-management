<template>
  <div class="contract-actions">
    <button type="button" class="btn print-btn" @click="$emit('print')">
      <span class="icon">🖨️</span>
      <span>طباعة نص العقد</span>
    </button>

    <label class="btn upload-btn" :class="{ disabled: uploadDisabled }">
      <span class="icon">📎</span>
      <span>ارفاق الملف</span>
      <input
        type="file"
        accept=".txt"
        :disabled="uploadDisabled"
        @change="onFile"
        hidden
      />
    </label>
  </div>
</template>

<script setup>
defineProps({
  uploadDisabled: { type: Boolean, default: false },
})

const emit = defineEmits(['print', 'upload'])

function onFile(e) {
  const file = e.target.files?.[0]
  if (file) emit('upload', file)
}
</script>

<style scoped>
.contract-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  direction: rtl;
  justify-content: flex-start;
  width: 100%;
  padding: 0.25rem 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.55rem 1.1rem;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  user-select: none;
  box-shadow: var(--shadow-sm);
}

.btn .icon {
  font-size: 1rem;
  line-height: 1;
}

/* ── Print button ───────────────────────── */
.print-btn {
  background: var(--color-primary-700);
  color: #fff;
}

.print-btn:hover {
  background: var(--color-primary-800);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.print-btn:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

/* ── Upload button ──────────────────────── */
.upload-btn {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1.5px solid var(--color-border-strong);
}

.upload-btn:hover {
  background: var(--color-primary-50);
  border-color: var(--color-primary-600);
  color: var(--color-primary-800);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.upload-btn:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

.upload-btn.disabled {
  opacity: 0.55;
  cursor: not-allowed;
  pointer-events: none;
}

/* ── Focus accessibility ────────────────── */
.btn:focus-visible {
  outline: 2px solid var(--color-primary-600);
  outline-offset: 2px;
}
</style>
