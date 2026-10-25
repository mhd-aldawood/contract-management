<template>
  <div class="form-field password-control">
    <label :for="id">{{ label }}</label>
    <div class="password-control__input-wrap">
      <input
        :id="id"
        :value="modelValue"
        :type="isVisible ? 'text' : 'password'"
        :autocomplete="autocomplete"
        :placeholder="placeholder"
        :required="required"
        :minlength="minlength"
        :disabled="disabled"
        dir="ltr"
        @input="emit('update:modelValue', $event.target.value)"
      />
      <button
        type="button"
        class="icon-button password-control__toggle"
        :aria-label="toggleLabel"
        :title="toggleLabel"
        :aria-pressed="isVisible"
        :disabled="disabled"
        @click="isVisible = !isVisible"
      >
        <svg
          v-if="!isVisible"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
          <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
          <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
          <line x1="1" y1="1" x2="23" y2="23" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  id: { type: String, required: true },
  label: { type: String, required: true },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'current-password' },
  required: { type: Boolean, default: false },
  minlength: { type: [Number, String], default: undefined },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const isVisible = ref(false)
const toggleLabel = computed(() => (isVisible.value ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'))
</script>

<style scoped>
.password-control > label {
  color: var(--color-text);
  font-size: 0.9rem;
  font-weight: 700;
}

.password-control__input-wrap {
  display: flex;
  align-items: center;
  direction: rtl;
  overflow: hidden;
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
}

.password-control__input-wrap:focus-within {
  border-color: var(--color-primary-600);
  box-shadow: var(--focus-ring);
}

.password-control__input-wrap input {
  flex: 1 1 0;
  width: 0;
  min-width: 0;
  min-height: 2.75rem;
  margin: 0;
  padding: 0.65rem 0.8rem;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  text-align: right;
}

.password-control__input-wrap input:-webkit-autofill,
.password-control__input-wrap input:-webkit-autofill:hover,
.password-control__input-wrap input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 1000px var(--color-surface) inset;
  -webkit-text-fill-color: var(--color-text);
  caret-color: var(--color-text);
}

.password-control__toggle.icon-button {
  flex: 0 0 2.75rem;
  display: inline-grid;
  place-items: center;
  width: 2.75rem;
  min-width: 2.75rem;
  height: 2.75rem;
  min-height: 2.75rem;
  margin: 0;
  padding: 0;
  color: var(--color-text-muted);
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.password-control__toggle.icon-button:hover {
  color: var(--color-primary-700);
  background: transparent;
}

.password-control__toggle svg {
  display: block;
  flex: 0 0 auto;
  pointer-events: none;
}
</style>
