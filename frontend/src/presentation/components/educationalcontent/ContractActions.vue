<template>
  <div class="contract-actions">
    <button type="button" class="btn print-btn" @click="$emit('print')">
      <span class="icon">🖨️</span>
      <span>طباعة نص العقد</span>
    </button>

    <label class="btn upload-btn">
      <span class="icon">📎</span>
      <span>ارفاق الملف</span>
      <input
        type="file"
        accept=".txt"
        @change="onFile"
        hidden
      />
    </label>
  </div>
</template>

<script setup>
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
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  user-select: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn .icon {
  font-size: 1rem;
  line-height: 1;
}

/* ── Print button ───────────────────────── */
.print-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.print-btn:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b3fa0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(102, 126, 234, 0.35);
}

.print-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.3);
}

/* ── Upload button ──────────────────────── */
.upload-btn {
  background: #ffffff;
  color: #4a5568;
  border: 1.5px solid #cbd5e0;
}

.upload-btn:hover {
  background: #f7fafc;
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(102, 126, 234, 0.15);
}

.upload-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(102, 126, 234, 0.1);
}

/* ── Focus accessibility ────────────────── */
.btn:focus-visible {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}
</style>