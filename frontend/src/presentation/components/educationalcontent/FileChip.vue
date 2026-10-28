<!-- src/presentation/components/FileChip.vue -->
<script setup>
defineProps({
  /** File name shown to the user (usually form.fileName). */
  fileName: {
    type: String,
    default: '',
  },
  /** Icon shown before the name. */
  icon: {
    type: String,
    default: '📎',
  },
  /** Show the remove (✕) button. */
  removable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['remove'])

function onRemove() {
  emit('remove')
}

</script>

<template>
  <div v-if="fileName" class="file-chip">
    <span class="file-icon" aria-hidden="true">{{ icon }}</span>

    <span class="file-name" :title="fileName">{{ fileName }}</span>


    <button
      v-if="removable"
      type="button"
      class="file-remove"
      title="إزالة الملف"
      aria-label="إزالة الملف"
      @click="onRemove"
    >
      ✕
    </button>
  </div>
</template>

<style scoped>
.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  background: var(--color-muted-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  font-size: 0.875rem;
  flex: 0 0 auto;
  max-width: 100%;
}

.file-icon {
  flex-shrink: 0;
}

.file-name {
  white-space: nowrap;
}

.file-remove {
  border: none;
  background: transparent;
  color: var(--color-danger);
  cursor: pointer;
  font-weight: bold;
  line-height: 1;
  padding: 0 0.15rem;
  flex-shrink: 0;
}

.file-remove:hover {
  color: #a62626;
}
</style>
