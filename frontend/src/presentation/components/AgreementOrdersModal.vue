<script setup>
import { downloadDocument } from '@/core/api/fileDownloads'
import { getAccessToken } from '@/core/api/authSession'

import container from '@/di/container'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { apiRequest } from '@/core/api/apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import BaseModal from '@/presentation/components/BaseModal.vue'

const props = defineProps({ agreement: { type: Object, default: null }, scope: { type: String, default: 'agreement' } })
const canDownload = computed(() => container.authRepository.hasPermission(props.scope === 'agreement' ? props.agreement?.feature : props.scope, 'download'))
const emit = defineEmits(['close', 'loaded'])
const orders = ref([])
const loading = ref(false)
const error = ref('')
const downloading = ref(null)
let version = 0
let controller
let downloadController
const headers = () => ({ Authorization: `Token ${getAccessToken()}` })
const dateTime = value => new Intl.DateTimeFormat('ar-SY-u-ca-gregory', {
  timeZone: 'Asia/Damascus', dateStyle: 'short', timeStyle: 'short',
}).format(new Date(value))

function cancel() {
  version++
  controller?.abort()
  downloadController?.abort()
  downloading.value = null
}
async function load() {
  cancel()
  orders.value = []
  error.value = ''
  const agreement = props.agreement
  loading.value = !!agreement
  if (!agreement) return
  const current = version
  controller = new AbortController()
  try {
    const response = await apiRequest(API_URLS.agreementOrders.list(agreement.feature, agreement.id, props.scope), {
      headers: headers(), signal: controller.signal,
    })
    if (current !== version) return
    orders.value = response.data
    emit('loaded', { key: agreement.key, count: response.data.length })
  } catch (e) { if (current === version && e.name !== 'AbortError') error.value = e.message }
  finally { if (current === version) loading.value = false }
}
async function download(order) {
  if (!props.agreement || downloading.value !== null) return
  const agreement = props.agreement
  const current = version
  downloading.value = order.id
  downloadController = new AbortController()
  error.value = ''
  try {
    await downloadDocument({ ...agreement, scope: props.scope, orderId: order.id, fileName: order.fileName, signal: downloadController.signal })
  } catch (e) { if (current === version && e.name !== 'AbortError') error.value = e.message }
  finally { if (current === version) downloading.value = null }
}
watch(() => [props.agreement?.key, props.scope], load, { immediate: true })
onBeforeUnmount(cancel)
</script>

<template>
  <BaseModal :model-value="!!agreement" title="أوامر الصرف المرتبطة بالاتفاقية" :description="agreement ? `${agreement.name} — ${agreement.agreementNumber}` : ''" size="lg" @update:model-value="emit('close')">
    <div class="panel-heading"><h3 class="agreement-orders-title" aria-live="polite">أوامر الصرف ({{ loading ? '…' : orders.length }})</h3><button type="button" class="btn--secondary btn--sm" :disabled="loading || downloading !== null" @click="load">تحديث القائمة</button></div>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <div class="table-scroll" :aria-busy="loading"><table class="agreement-orders-table"><thead><tr><th>أمر الصرف</th><th>الملف</th><th>تاريخ الرفع</th><th>الإجراء</th></tr></thead><tbody>
      <tr v-if="loading"><td colspan="4" class="empty-state">جارٍ تحميل أوامر الصرف…</td></tr>
      <tr v-else-if="error && !orders.length"><td colspan="4" class="empty-state"><button type="button" class="btn--secondary" @click="load">إعادة المحاولة</button></td></tr>
      <tr v-else-if="!orders.length"><td colspan="4" class="empty-state">لا توجد أوامر صرف حالية لهذه الاتفاقية.</td></tr>
      <tr v-for="order in orders" :key="order.id"><td data-label="أمر الصرف"><strong>{{ order.title || order.fileName }}</strong><p v-if="order.notes" class="agreement-order-note">{{ order.notes }}</p></td><td data-label="الملف">{{ order.fileName }}<small class="agreement-order-meta">{{ order.fileSize < 1024 ? `${order.fileSize} B` : `${(order.fileSize / 1024).toFixed(1)} KB` }}</small></td><td data-label="تاريخ الرفع">{{ dateTime(order.createdAt) }}<small class="agreement-order-meta">{{ order.uploadedBy || '—' }}</small></td><td data-label="الإجراء"><button type="button" class="btn--secondary btn--sm" :disabled="downloading !== null || !canDownload" @click="download(order)">{{ downloading === order.id ? 'جارٍ التنزيل…' : 'تنزيل' }}</button></td></tr>
    </tbody></table></div>
  </BaseModal>
</template>

<style scoped>
.agreement-orders-title { margin: 0; font-size: 1rem; }
.agreement-orders-table { min-width: 42rem; }
.agreement-orders-table td:first-child { min-width: 12rem; max-width: 28rem; }
.agreement-orders-table td { white-space: normal; overflow-wrap: anywhere; }
.agreement-order-note { margin: 0.4rem 0 0; white-space: pre-wrap; color: var(--color-text-muted); line-height: 1.7; }
.agreement-order-meta { display: block; margin-block-start: 0.35rem; color: var(--color-text-muted); }
@media (max-width: 640px) {
  .panel-heading { flex-wrap: wrap; }
  .table-scroll { border: 0; overflow: visible; }
  .agreement-orders-table { display: block; min-width: 0; }
  .agreement-orders-table thead { display: none; }
  .agreement-orders-table tbody { display: grid; gap: 1rem; }
  .agreement-orders-table tr { display: grid; min-width: 0; padding: 0.6rem 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
  .agreement-orders-table td, .agreement-orders-table td:first-child { display: block; min-width: 0; max-width: none; padding: 0.65rem 0; border: 0; }
  .agreement-orders-table td[data-label]::before { content: attr(data-label); display: block; margin-block-end: 0.4rem; color: var(--color-text-muted); font-size: 0.8rem; font-weight: 700; }
  .agreement-orders-table td:last-child button { width: 100%; }
}
</style>
