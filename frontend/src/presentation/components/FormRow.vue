<template>
  <div class="contract-field" :class="{ 'contract-field--wide': wide, 'contract-field--invalid': !!error }">
      <label :for="inputId" class="contract-field__label">
        {{ label }}
        <span v-if="required" class="req-mark" aria-hidden="true">*</span>
      </label>
      <div class="form-input">
        <slot :input-id="inputId" :error-id="error ? errorId : undefined" />
        <p v-if="error" :id="errorId" class="field-error" role="alert">
          <span>{{ error }}</span>
        </p>
      </div>
  </div>
</template>

<script setup>
import { useId } from 'vue'

defineProps({
  label:    { type: String,  default: '' },
  error:    { type: String,  default: '' },
  required: { type: Boolean, default: false },
  wide: { type: Boolean, default: false },
})
const inputId = `contract-field-${useId()}`
const errorId = `${inputId}-error`
</script>

<style scoped>
.contract-field { display: grid; align-content: start; gap: 0.5rem; min-width: 0; }
.contract-field--wide { grid-column: 1 / -1; }
.contract-field__label { font-size: 0.9rem; font-weight: 700; line-height: 1.6; }
.form-input { display: grid; align-content: start; gap: 0.5rem; min-width: 0; }
.form-input :deep(input), .form-input :deep(select), .form-input :deep(textarea) { min-width: 0; }
.form-input :deep(.is-invalid) { border-color: var(--color-danger); background: var(--color-danger-bg); }
.req-mark, .field-error { color: var(--color-danger); }
.field-error { margin: 0; font-size: 0.85rem; line-height: 1.6; }
</style>
