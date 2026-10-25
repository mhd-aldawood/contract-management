import { computed } from 'vue'
import container from '@/di/container'

export function useFeatureAccess(feature) {
  const canRead = computed(() =>
    container.authRepository.hasPermission(feature, 'read')
  )
  const canWrite = computed(() =>
    container.authRepository.hasPermission(feature, 'write')
  )

  return { canRead, canWrite }
}
