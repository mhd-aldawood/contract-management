// src/presentation/composables/useFormValidation.js
import { reactive, ref, computed } from 'vue'

/**
 * @param {object} form    reactive form object (must be `reactive(...)`, not `ref`)
 * @param {object} schema  { fieldName: [ruleFn, ...] }
 */
export function useFormValidation(form, schema) {
  const fields = Object.keys(schema)

  const touched = reactive({})
  const submitted = ref(false)

  function getFieldError(field) {
    for (const rule of schema[field] ?? []) {
      const msg = rule(form[field], form)
      if (msg) return msg
    }
    return ''
  }

  /** All errors, always computed (so they update live) */
  const errors = computed(() => {
    const out = {}
    for (const f of fields) out[f] = getFieldError(f)
    return out
  })

  /** Errors only for fields the user has touched / after a submit attempt */
  const visibleErrors = computed(() => {
    const out = {}
    for (const f of fields) {
      out[f] = submitted.value || touched[f] ? errors.value[f] : ''
    }
    return out
  })

  const isValid = computed(() => fields.every((f) => !errors.value[f]))

  const firstError = computed(
    () => fields.map((f) => errors.value[f]).find(Boolean) || ''
  )

  function touch(field) {
    touched[field] = true
  }

  function touchAll() {
    fields.forEach((f) => { touched[f] = true })
  }

  /** Call on submit. Returns true when the whole form is valid. */
  // function validate() {
  //   submitted.value = true
  //   return isValid.value
  // }

  function reset() {
    fields.forEach((f) => { touched[f] = false })
    submitted.value = false
  }

  return {
    errors, visibleErrors, isValid, firstError,
    touched, submitted,
    touch, touchAll, reset,
  }
}