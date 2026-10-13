<template>
  <tr>
    <td class="form-row-cell" :class="{ 'row-invalid': !!error }">
      <div class="form-input">
        <slot />
        <p v-if="error" class="field-error" role="alert">
          <span class="err-icon">⚠</span>
          <span>{{ error }}</span>
        </p>
      </div>
      <label class="form-label">
        {{ label }}
        <span v-if="required" class="req-mark" aria-hidden="true">*</span>
      </label>
    </td>
  </tr>
</template>

<script setup>
defineProps({
  label:    { type: String,  default: '' },
  error:    { type: String,  default: '' },
  required: { type: Boolean, default: false },
})
</script>

<style scoped>
.form-row-cell {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #ddd;
  gap: 0;
}

.form-label {
  width: 200px;
  text-align: right;
  font-weight: bold;
  background: #f7fafc;
  padding: 0.4rem 0.6rem;
  margin: 0;
  border-left: 1px solid #ddd;
  flex-shrink: 0;
}

.req-mark {
  color: #e53e3e;
  margin-inline-start: 4px;
  font-weight: bold;
}

.form-input {
  flex: 1;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: stretch;
}

/* ✅ :deep() is required to reach slotted inputs */
.form-input :deep(input),
.form-input :deep(select),
.form-input :deep(textarea) {
  width: 100%;
  padding: 0.4rem 0.6rem;
  border: none;
  border-radius: 0;
  font-size: 0.95rem;
  outline: none;
  box-sizing: border-box;
  direction: rtl !important;
  text-align: right !important;
}

/* ✅ Ensure placeholder starts from the right */
.form-input :deep(input::placeholder),
.form-input :deep(textarea::placeholder) {
  text-align: right !important;
  direction: rtl !important;
}

/* ✅ Invalid state highlight (border lives on the input itself) */
.form-input :deep(input.is-invalid),
.form-input :deep(select.is-invalid),
.form-input :deep(textarea.is-invalid) {
  background: #fff5f5;
  box-shadow: inset 0 0 0 1px #e53e3e;
}

/* ✅ Error message */
.field-error {
  margin: 0;
  color: #e53e3e;
  font-size: 0.8rem;
  line-height: 1.2;
  text-align: right;
  direction: rtl;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.err-icon {
  font-size: 0.85rem;
}

/* ✅ Highlight row label when invalid */
.row-invalid .form-label {
  background: #fff5f5;
  color: #c53030;
}
</style>