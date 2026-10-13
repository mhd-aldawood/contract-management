// src/presentation/composables/useEducationalContentForm.js
import { ref, reactive, computed } from 'vue'
import EducationalContent from '@/domain/entities/EducationalContent'
import container from '@/di/container'
import { createLogger } from '@/core/logger'
import { useFormValidation } from '@/presentation/composables/useFormValidation'
import {
  educationalContentSchema,
  validatePaymentSchedule,
} from '@/presentation/validation/educationalContentSchema'

const log = createLogger('useEducationalContentForm')

export function useEducationalContentForm(type = 'educational-content') {
  const form = reactive(EducationalContent.empty(type))
  const saving = ref(false)
  const error = ref('')

  /* ---------- validation ---------- */
  const {
    visibleErrors,
    isValid,
    firstError,
    touch,
    touchAll,
    reset: resetValidation,
  } = useFormValidation(form, educationalContentSchema)

  /** Per-row errors for the payment schedule table */
  const paymentErrors = computed(() =>
    validatePaymentSchedule(form.paymentSchedule || [])
  )

  const hasPaymentErrors = computed(() =>
    paymentErrors.value.some((row) => Object.keys(row).length > 0)
  )

  const isFormValid = computed(() => isValid.value && !hasPaymentErrors.value)

  /* ---------- mutation helpers ---------- */
  function reset() {
    Object.assign(form, EducationalContent.empty(type))
    error.value = ''
    resetValidation()
  }

  function toggleContentVisibility() {
    form.isHidden = !form.isHidden
  }

  function addPaymentRow() {
    form.paymentSchedule.push({ label: '', amount: 0, dueDate: '' })
    touch('paymentSchedule')
  }

  function removePaymentRow(index) {
    form.paymentSchedule.splice(index, 1)
    touch('paymentSchedule')
  }

  function handleFormUpload(payload) {
    const picked =
      payload instanceof File          ? payload :
      payload?.target?.files?.[0]      ? payload.target.files[0] :
      payload?.file                    ? payload.file :
      Array.isArray(payload)           ? payload[0] :
      null

    if (!picked) {
      log.warn('handleUpload: no file found in payload', payload)
      return
    }

    form.fileName = picked.name
    form.fileUrl = picked.fileUrl
    form.file = picked
    log.debug('handleUpload: file set', picked.name, picked.size, picked.type)
  }

  function clearFile() {
    form.fileName = ''
    form.fileUrl = ''
    form.file = null
  }

  /* ---------- save with validation gate ---------- */
  async function save() {
    error.value = ''

    if (!isFormValid.value) {
      touchAll()
      error.value = firstError.value || 'يرجى تصحيح بيانات الدفعات'
      const err = new Error(error.value)
      err.name = 'ValidationError'
      throw err
    }

    saving.value = true
    try {
      log.debug('useEducationalContentForm save func', form)
      const response = await container.saveEducationalContentUseCase.execute(form)
      const saved = response?.data ?? response
      if (saved) Object.assign(form, saved instanceof EducationalContent ? saved.toJSON() : saved)
      resetValidation()
      return response
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      saving.value = false
    }
  }

  return {
    form,
    saving,
    error,
    handleFormUpload,
    toggleContentVisibility,
    save,
    reset,
    clearFile,
    addPaymentRow,
    removePaymentRow,

    // ✅ validation API
    visibleErrors,
    paymentErrors,
    isFormValid,
    touch,
  }
}
