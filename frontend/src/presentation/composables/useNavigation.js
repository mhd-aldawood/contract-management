// src/presentation/composables/useNavigation.js
import { useRouter } from 'vue-router'
import { NAV_ITEMS } from '@/presentation/config/navigation'
import container from '@/di/container'

export function useNavigation() {
  const router = useRouter()

  function navigate(item) {
    if (item.children) return
    router.push(item.path)
  }

  const visibleItems = NAV_ITEMS
    .map((item) => item.children
      ? {
          ...item,
          children: item.children.filter((child) =>
            container.authRepository.hasPermission(child.feature, 'read')
          ),
        }
      : item)
    .filter((item) => {
      if (item.adminOnly && !container.authRepository.isAdmin()) return false
      if (item.children) return item.children.length > 0
      return !item.feature || container.authRepository.hasPermission(item.feature, 'read')
    })

  return {
    visibleItems,
    navigate,
  }
}
