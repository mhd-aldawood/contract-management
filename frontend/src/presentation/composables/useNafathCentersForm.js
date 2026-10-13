// src/presentation/composables/useNafathCentersForm.js
import { reactive, ref, computed } from 'vue';
import { NafathCenter } from '@/domain/entities/NafathCenter';
import { nafathCentersSchema } from '@/presentation/validation/nafathCentersSchema';
import  container  from '@/di/container';
import { createLogger } from '@/core/logger'
import { useFormValidation } from '@/presentation/composables/useFormValidation'

import {
  validatePaymentSchedule,
} from '@/presentation/validation/validatePaymentSchedule'
const logger = createLogger('useNafathCentersForm')

export function useNafathCentersForm(type = 'nafath-center') {
  const form = reactive( NafathCenter.empty(type));
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
  } = useFormValidation(form, nafathCentersSchema)

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
      Object.assign(form, NafathCenter.empty(type))
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
        logger.warn('handleUpload: no file found in payload', payload)
        return
      }
  
      form.fileName = picked.name
      form.fileUrl = picked.fileUrl
      form.file = picked
      logger.debug('handleUpload: file set', picked.name, picked.size, picked.type)
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
        logger.debug('useNafathCentersForm save func', form)
        const response = await container.saveNafathCenterUseCase.execute(form)
        const saved = response?.data ?? response
        if (saved) Object.assign(form, saved instanceof NafathCenter ? saved.toJSON() : saved)
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
