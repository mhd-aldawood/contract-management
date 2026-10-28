<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modelValue"
        class="base-modal__backdrop"
        role="presentation"
        @mousedown.self="requestClose"
      >
        <section
          ref="dialog"
          class="base-modal"
          :class="`base-modal--${size}`"
          role="dialog"
          dir="rtl"
          aria-modal="true"
          :aria-labelledby="titleId"
          :aria-describedby="description ? descriptionId : undefined"
          tabindex="-1"
          @keydown.esc.stop="requestClose"
          @keydown.tab="trapFocus"
        >
          <header class="base-modal__header">
            <div>
              <p v-if="eyebrow" class="base-modal__eyebrow">{{ eyebrow }}</p>
              <h2 :id="titleId">{{ title }}</h2>
              <p v-if="description" :id="descriptionId" class="base-modal__description">{{ description }}</p>
            </div>
            <button
              type="button"
              class="icon-button"
              aria-label="إغلاق النافذة"
              :disabled="busy"
              @click="requestClose"
            >
              ✕
            </button>
          </header>

          <div class="base-modal__body">
            <slot />
          </div>

          <footer class="base-modal__footer">
            <div :id="actionsId" class="base-modal__primary-actions"></div>
            <slot name="footer">
              <button type="button" class="btn--secondary" :disabled="busy" @click="requestClose">إغلاق</button>
            </slot>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
const openDialogs = new Set()
</script>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, provide, ref, useId, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: '' },
  size: { type: String, default: 'md', validator: value => ['sm', 'md', 'lg', 'xl'].includes(value) },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'close'])
const id = useId()
const titleId = `modal-title-${id}`
const descriptionId = `modal-description-${id}`
const actionsId = `modal-actions-${id}`
provide('modal-actions-target', `#${actionsId}`)
const dialog = ref(null)
let previousFocus = null

function trapFocus(event) {
  const elements = Array.from(dialog.value?.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex="0"]') || []).filter(element => element.offsetParent !== null)
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (!first) { event.preventDefault(); return }
  if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.value)) { event.preventDefault(); last.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
}

function requestClose() {
  if (props.busy) return
  emit('update:modelValue', false)
  emit('close')
}

function handleEscape(event) {
  // Downloads or refreshed content can move focus out of the dialog.
  if (event.key === 'Escape' && !event.defaultPrevented && props.modelValue && [...openDialogs].at(-1) === id) {
    event.preventDefault()
    requestClose()
  }
}

function releaseScrollLock() {
  openDialogs.delete(id)
  document.body.classList.toggle('modal-open', openDialogs.size > 0)
}

watch(() => props.modelValue, async (open) => {
  if (open) openDialogs.add(id)
  else openDialogs.delete(id)
  document.body.classList.toggle('modal-open', openDialogs.size > 0)
  if (open) {
    previousFocus = document.activeElement
    await nextTick()
    dialog.value?.focus()
  } else previousFocus?.focus?.()
}, { immediate: true })

onMounted(() => document.addEventListener('keydown', handleEscape))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscape)
  releaseScrollLock()
})
</script>
