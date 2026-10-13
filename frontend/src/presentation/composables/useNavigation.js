// src/presentation/composables/useNavigation.js
import { useRouter } from 'vue-router'
import { NAV_ITEMS } from '@/presentation/config/navigation'

export function useNavigation() {
  const router = useRouter()

  function navigate(item) {
    if (item.children) return
    router.push(item.path)
  }

  return {
    visibleItems: NAV_ITEMS,
    navigate,
  }
}