import { validCostTable } from '@/presentation/utils/agreementCosts'
import { reactive, ref, computed } from 'vue';
import { OtherAgreement } from '@/domain/entities/OtherAgreement';
import { otherAgreementSchema } from '@/presentation/validation/otherAgreementSchema';
import  container  from '@/di/container';
import { createLogger } from '@/core/logger'
import { useFormValidation } from '@/presentation/composables/useFormValidation'

const logger = createLogger('useOtherAgreementForm')


export function useOtherAgreementForm(type = 'other-agreement') {
  const form = reactive( OtherAgreement.empty(type));
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
  } = useFormValidation(form, otherAgreementSchema)

  const isFormValid = computed(() => isValid.value && validCostTable(form))

  /* ---------- mutation helpers ---------- */
    function reset() {
      Object.assign(form, OtherAgreement.empty(type))
      error.value = ''
      resetValidation()
    }
  
    function toggleContentVisibility() {
      form.isHidden = !form.isHidden
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
        logger.debug('useOtherAgreements save func', form)
        const response = await container.saveOtherUseCase.execute(form)
        const saved = response?.data ?? response
        if (saved) Object.assign(form, saved instanceof OtherAgreement ? saved.toJSON() : saved)
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
      isFormValid,
      touch,
      visibleErrors
    }
  
}
