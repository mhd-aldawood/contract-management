<template>
  <div class="notification-host" aria-live="polite" aria-atomic="true">
    <TransitionGroup name="notification">
      <div
        v-for="item in notifications"
        :key="item.id"
        class="notification"
        :class="`notification--${item.type}`"
        :role="item.type === 'error' ? 'alert' : 'status'"
      >
        <span class="notification__icon" aria-hidden="true">
          {{ item.type === 'success' ? '✓' : '!' }}
        </span>
        <span class="notification__message">{{ item.message }}</span>
        <button
          class="notification__close"
          type="button"
          aria-label="إغلاق الرسالة"
          @click="remove(item.id)"
        >
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useNotifications } from '@/presentation/composables/useNotifications'

const { notifications, remove } = useNotifications()
</script>

<style scoped>
.notification-host {
  position: fixed;
  inset-block-start: 1rem;
  inset-inline-start: 1rem;
  z-index: 10000;
  display: grid;
  gap: 0.75rem;
  width: min(26rem, calc(100vw - 2rem));
  pointer-events: none;
  direction: rtl;
}

.notification {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  color: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 10px 30px rgb(15 23 42 / 24%);
  pointer-events: auto;
}

.notification--success { background: #15803d; }
.notification--error { background: #b91c1c; }

.notification__icon {
  display: grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  font-weight: 800;
  border: 2px solid currentColor;
  border-radius: 999px;
}

.notification__message {
  line-height: 1.5;
  text-align: right;
}

.notification__close {
  padding: 0.15rem 0.35rem;
  color: inherit;
  font-size: 1.4rem;
  line-height: 1;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.notification-enter-active,
.notification-leave-active { transition: 180ms ease; }
.notification-enter-from,
.notification-leave-to { opacity: 0; transform: translateY(-0.5rem); }
</style>
