import { reactive } from 'vue'

const notifications = reactive([])
let nextId = 1

function remove(id) {
  const index = notifications.findIndex((item) => item.id === id)
  if (index !== -1) notifications.splice(index, 1)
}

function show(type, message, duration = 5000) {
  if (!message) return null

  const notification = { id: nextId++, type, message }
  notifications.push(notification)

  if (duration > 0) {
    window.setTimeout(() => remove(notification.id), duration)
  }

  return notification.id
}

export function useNotifications() {
  return {
    notifications,
    remove,
    success: (message, duration) => show('success', message, duration),
    error: (message, duration) => show('error', message, duration),
  }
}
