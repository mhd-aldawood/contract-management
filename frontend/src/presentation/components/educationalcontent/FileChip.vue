<!-- src/presentation/components/FileChip.vue -->
<script setup>
defineProps({
  /** File name shown to the user (usually form.fileName). */
  fileName: {
    type: String,
    default: '',
  },
  /** Optional server URL. Shows the "تحميل" link when set. */
  fileUrl: {
    type: String,
    default: '',
  },
  /** Icon shown before the name. */
  icon: {
    type: String,
    default: '📎',
  },
  /** Label of the download link. */
  downloadLabel: {
    type: String,
    default: 'تحميل',
  },
  /** Show the remove (✕) button. */
  removable: {
    type: Boolean,
    default: true,
  },
  /** Show the download link when fileUrl exists. */
  downloadable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['remove', 'download'])

function onRemove() {
  emit('remove')
}

function onDownload(event) {
  emit('download', { url: event.currentTarget.href })
}
</script>

<template>
  <div v-if="fileName" class="file-chip">
    <span class="file-icon" aria-hidden="true">{{ icon }}</span>

    <span class="file-name" :title="fileName">{{ fileName }}</span>

    <!-- <a
      v-if="downloadable && fileUrl"
      :href="fileUrl"
      target="_blank"
      rel="noopener"
      class="file-link"
      @click="onDownload"
    >
      {{ downloadLabel }}
    </a> -->

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
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
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

.file-link {
  color: #2563eb;
  text-decoration: none;
  white-space: nowrap;
}

.file-link:hover {
  text-decoration: underline;
}

.file-remove {
  border: none;
  background: transparent;
  color: #ef4444;
  cursor: pointer;
  font-weight: bold;
  line-height: 1;
  padding: 0 0.15rem;
  flex-shrink: 0;
}

.file-remove:hover {
  color: #b91c1c;
}
</style>