<script setup>
import { downloadDocument } from '@/core/api/fileDownloads'
import { getAccessToken } from '@/core/api/authSession'

import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { API_URLS } from '@/core/config/apiUrls'
import { apiRequest } from '@/core/api/apiClient'
import { CONTRACT_TYPES } from '@/presentation/config/contracts'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
import { useNotifications } from '@/presentation/composables/useNotifications'
import PageHeader from '@/presentation/components/PageHeader.vue'

const { canWrite, canDownload } = useFeatureAccess('finance')
const route = useRoute()
const notify = useNotifications()
const agreements = ref([])
const query = ref('')
const financeOrders = ref('')
const kind = ref(CONTRACT_TYPES.some(type => type.feature === route.query.type) ? route.query.type : '')
const loading = ref(false)
const error = ref('')
const selected = ref(null)
const orders = ref([])
const ordersLoading = ref(false)
const orderError = ref('')
const busy = ref(false)
const picked = ref([])
const uploadInput = ref(null)
const ordersPanel = ref(null)
const editingOrder = ref(null)
const editForm = reactive({ title: '', notes: '' })
let ordersRequest = 0
const pendingRemoval = ref(null)
const page = ref(1)
const pageSize = 15
const allowed = '.pdf,.png,.jpg,.jpeg,.doc,.docx,.xls,.xlsx,.txt'
const headers = () => ({ Authorization: `Token ${getAccessToken()}` })
const filtered = computed(() => agreements.value.filter(agreement =>
  (!kind.value || agreement.feature === kind.value) &&
  (!financeOrders.value || (agreement.orderCount > 0) === (financeOrders.value === 'with')) &&
  `${agreement.name} ${agreement.agreementNumber}`.toLowerCase().includes(query.value.trim().toLowerCase())))
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const rows = computed(() => filtered.value.slice((Math.min(page.value, pages.value) - 1) * pageSize, Math.min(page.value, pages.value) * pageSize))

async function load() {
  if (busy.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiRequest(API_URLS.finance.agreements, { headers: headers() })
    agreements.value = response.data
    if (selected.value) {
      const agreement = agreements.value.find(item => item.key === selected.value.key)
      if (agreement) {
        selected.value = agreement
        await loadOrders()
      } else closeOrders()
    }
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function openOrders(agreement) {
  if (busy.value || loading.value) return
  selected.value = agreement
  orders.value = []
  picked.value = []
  pendingRemoval.value = null
  editingOrder.value = null
  orderError.value = ''
  if (uploadInput.value) uploadInput.value.value = ''
  await nextTick()
  ordersPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  await loadOrders()
}

function changeDocument(key) {
  if (busy.value || loading.value) return
  const agreement = agreements.value.find(item => item.key === key)
  if (agreement) openOrders(agreement)
  else closeOrders()
}

async function loadOrders() {
  const agreement = selected.value
  if (!agreement) return
  const requestId = ++ordersRequest
  ordersLoading.value = true
  orderError.value = ''
  try {
    const response = await apiRequest(API_URLS.finance.orders(agreement.feature, agreement.id), { headers: headers() })
    if (requestId !== ordersRequest || selected.value?.key !== agreement.key) return
    orders.value = response.data
    agreement.orderCount = response.data.length
  } catch (e) { if (requestId === ordersRequest && selected.value?.key === agreement.key) orderError.value = e.message }
  finally { if (requestId === ordersRequest) ordersLoading.value = false }
}

function closeOrders() {
  if (busy.value) return
  selected.value = null
  ordersRequest++
  ordersLoading.value = false
  orders.value = []
  orderError.value = ''
  picked.value = []
  pendingRemoval.value = null
  editingOrder.value = null
}

function editOrder(order) {
  if (busy.value) return
  editingOrder.value = order.id
  pendingRemoval.value = null
  Object.assign(editForm, { title: order.title || order.fileName, notes: order.notes || '' })
}

async function saveOrderMetadata() {
  if (!canWrite.value || busy.value || !selected.value || !editingOrder.value || !editForm.title.trim()) return
  busy.value = true
  orderError.value = ''
  try {
    const response = await apiRequest(API_URLS.finance.order(selected.value.feature, selected.value.id, editingOrder.value), {
      method: 'PATCH', headers: headers(), body: JSON.stringify({ title: editForm.title.trim(), notes: editForm.notes.trim() }),
    })
    editingOrder.value = null
    notify.success(response.message)
    await loadOrders()
  } catch (e) { orderError.value = e.message }
  finally { busy.value = false }
}

function validateFiles(files) {
  if (!files.length) throw new Error('اختر ملفاً واحداً على الأقل')
  if (files.length > 20 || files.reduce((total, file) => total + file.size, 0) > 19 * 1024 * 1024) throw new Error('الحد الأقصى 20 ملفاً بحجم إجمالي 19 ميغابايت')
  const extensions = allowed.split(',')
  if (files.some(file => !file.size || !extensions.includes(`.${file.name.split('.').pop().toLowerCase()}`))) throw new Error('اختر ملفات غير فارغة بصيغة PDF أو صور أو Word أو Excel أو TXT')
}

async function uploadFiles() {
  if (!selected.value || !canWrite.value || busy.value) return
  try { validateFiles(picked.value) } catch (e) { orderError.value = e.message; return }
  busy.value = true
  orderError.value = ''
  try {
    const body = new FormData()
    picked.value.forEach(file => body.append('files', file))
    const response = await apiRequest(API_URLS.finance.orders(selected.value.feature, selected.value.id), { method: 'POST', body, headers: headers() })
    picked.value = []
    if (uploadInput.value) uploadInput.value.value = ''
    notify.success(response.message)
    await loadOrders()
  } catch (e) { orderError.value = e.message }
  finally { busy.value = false }
}

async function replaceFile(order, event) {
  const input = event.target
  const files = Array.from(input.files || [])
  if (!files.length || !canWrite.value || busy.value) return
  try { validateFiles(files) } catch (e) { orderError.value = e.message; input.value = ''; return }
  busy.value = true
  orderError.value = ''
  try {
    const body = new FormData()
    body.append('file', files[0])
    const response = await apiRequest(API_URLS.finance.order(selected.value.feature, selected.value.id, order.id), { method: 'PATCH', body, headers: headers() })
    notify.success(response.message)
    await loadOrders()
  } catch (e) { orderError.value = e.message }
  finally { busy.value = false; input.value = '' }
}

async function removeOrder() {
  if (!pendingRemoval.value || !canWrite.value || busy.value) return
  busy.value = true
  orderError.value = ''
  try {
    const response = await apiRequest(API_URLS.finance.order(selected.value.feature, selected.value.id, pendingRemoval.value.id), { method: 'DELETE', headers: headers() })
    pendingRemoval.value = null
    notify.success(response.message)
    await loadOrders()
  } catch (e) { orderError.value = e.message }
  finally { busy.value = false }
}

async function downloadOrder(order) {
  if (busy.value) return
  busy.value = true
  orderError.value = ''
  try {
    await downloadDocument({ ...selected.value, scope: 'finance', orderId: order.id, fileName: order.fileName })
  } catch (e) { orderError.value = e.message }
  finally { busy.value = false }
}

function fileSize(bytes) { return `${(bytes / 1024).toFixed(1)} KB` }
function dateTime(value) {
  return new Intl.DateTimeFormat('ar-SY-u-ca-gregory', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Damascus' }).format(new Date(value))
}
onMounted(async () => {
  await load()
  const agreement = agreements.value.find(item => item.key === route.query.document)
  if (agreement) await openOrders(agreement)
})
</script>

<template>
  <main class="app-page finance-page" dir="rtl">
    <PageHeader title="المالية وأوامر الصرف" eyebrow="إدارة العقود والاتفاقيات" description="اختر عقداً أو اتفاقية لعرض أوامر الصرف المرفوعة وإدارتها.">
      <template #actions><button type="button" class="btn--secondary" :disabled="loading || busy" @click="load">تحديث</button></template>
    </PageHeader>
    <section class="panel">
      <div class="filters">
        <label class="form-field"><span>البحث</span><input v-model="query" type="search" placeholder="اسم العقد أو رقم الاتفاقية" @input="page = 1" /></label>
        <label class="form-field"><span>نوع الاتفاقية</span><select v-model="kind" @change="page = 1"><option value="">جميع الأنواع</option><option v-for="type in CONTRACT_TYPES" :key="type.feature" :value="type.feature">{{ type.title }}</option></select></label>
        <label class="form-field"><span>أوامر الصرف</span><select v-model="financeOrders" @change="page = 1"><option value="">الكل</option><option value="with">لديها أوامر صرف</option><option value="without">بدون أوامر صرف</option></select></label>
        <button type="button" class="btn--secondary" @click="query = ''; kind = ''; financeOrders = ''; page = 1">إلغاء الفلاتر</button>
      </div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p class="result-count" aria-live="polite">عدد العقود والاتفاقيات: {{ filtered.length }}</p>
      <div class="table-scroll" :aria-busy="loading">
        <table class="finance-agreements"><thead><tr><th>اسم العقد / الاتفاقية</th><th>الرقم</th><th>التفاصيل</th></tr></thead>
          <tbody><tr v-if="loading"><td colspan="3" class="empty-state">جارٍ التحميل…</td></tr>
            <tr v-else-if="!rows.length"><td colspan="3" class="empty-state">لا توجد عقود أو اتفاقيات تطابق البحث.</td></tr>
            <tr v-for="agreement in loading ? [] : rows" :key="agreement.key" class="finance-agreement-row" :class="{ 'finance-agreement-row--selected': selected?.key === agreement.key }" :tabindex="busy ? -1 : 0" :aria-selected="selected?.key === agreement.key" :aria-disabled="busy || undefined" @click="openOrders(agreement)" @keydown.enter.self="openOrders(agreement)" @keydown.space.self.prevent="openOrders(agreement)">
              <td><strong>{{ agreement.name || '—' }}</strong><small class="finance-category">{{ agreement.category }}</small></td><td>{{ agreement.agreementNumber || '—' }}</td>
              <td><p class="finance-agreement-summary">{{ agreement.details || '—' }}</p><button type="button" class="btn--secondary btn--sm" :disabled="busy" :aria-pressed="selected?.key === agreement.key" aria-controls="finance-orders" @click.stop="openOrders(agreement)">أوامر الصرف ({{ agreement.orderCount }})</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <nav class="finance-pagination" aria-label="صفحات المالية"><button type="button" class="btn--secondary btn--sm" :disabled="page <= 1" @click="page--">السابق</button><span>صفحة {{ Math.min(page, pages) }} من {{ pages }}</span><button type="button" class="btn--secondary btn--sm" :disabled="page >= pages" @click="page++">التالي</button></nav>
    </section>

    <section id="finance-orders" ref="ordersPanel" class="panel finance-orders-panel" aria-labelledby="finance-orders-title">
      <header class="panel-heading finance-orders-heading">
        <div><h2 id="finance-orders-title">أوامر الصرف</h2><p v-if="selected" class="finance-selected-document">{{ selected.name }} — رقم {{ selected.agreementNumber || '—' }}</p><p v-else class="finance-selected-document">اختر عقداً أو اتفاقية من الجدول أعلاه لعرض أوامر الصرف الخاصة بها.</p></div>
        <label class="form-field finance-document-selector"><span>العقد / الاتفاقية</span><select :value="selected?.key || ''" :disabled="busy || loading" @change="changeDocument($event.target.value)"><option value="">اختر العقد أو الاتفاقية</option><option v-for="agreement in agreements" :key="agreement.key" :value="agreement.key">{{ agreement.name }} — {{ agreement.agreementNumber }} ({{ agreement.category }})</option></select></label>
        <button v-if="selected" type="button" class="btn--secondary btn--sm" :disabled="busy" @click="closeOrders">إلغاء التحديد</button>
      </header>
      <section v-if="selected && canWrite" :key="selected.key" class="finance-upload">
        <h3>إضافة أوامر صرف</h3>
        <label class="form-field"><span>ملفات أوامر الصرف</span><input ref="uploadInput" type="file" multiple :accept="allowed" :disabled="busy || ordersLoading" @change="picked = Array.from($event.target.files || [])" /><small class="field-hint">يمكن اختيار أكثر من ملف. PDF، صور، Word، Excel، TXT. حتى 20 ملفاً بحجم إجمالي 19 ميغابايت.</small></label>
        <ul v-if="picked.length" class="picked-files"><li v-for="(file, index) in picked" :key="index">{{ file.name }} — {{ fileSize(file.size) }}</li></ul>
        <button type="button" :disabled="!picked.length || busy || ordersLoading" @click="uploadFiles">{{ busy ? 'جارٍ التنفيذ…' : `رفع الملفات (${picked.length})` }}</button>
      </section>
      <p v-else-if="selected" class="notice">لديك صلاحية عرض وتنزيل أوامر الصرف فقط.</p>
      <p v-if="orderError" class="error" role="alert">{{ orderError }}</p>
      <div class="panel-heading"><h3 aria-live="polite">أوامر الصرف المرفوعة ({{ selected && !ordersLoading ? orders.length : '—' }})</h3><button v-if="selected" type="button" class="btn--secondary btn--sm" :disabled="busy || ordersLoading" @click="loadOrders">تحديث القائمة</button></div>
      <div class="table-scroll" :aria-busy="ordersLoading"><table class="finance-orders"><thead><tr><th>الملف</th><th>تاريخ الرفع</th><th>آخر تحديث</th><th>بواسطة</th><th>الإجراءات</th></tr></thead>
        <tbody><tr v-if="!selected"><td colspan="5" class="empty-state">لم يتم تحديد اتفاقية.</td></tr><tr v-else-if="ordersLoading"><td colspan="5" class="empty-state">جارٍ تحميل أوامر الصرف…</td></tr><tr v-else-if="!orders.length"><td colspan="5" class="empty-state">لم تُرفع أوامر صرف لهذه الاتفاقية بعد.</td></tr>
          <template v-for="order in !selected || ordersLoading ? [] : orders" :key="order.id"><tr><td class="finance-file-name"><strong>{{ order.title || order.fileName }}</strong><small class="finance-category">{{ order.fileName }} — {{ fileSize(order.fileSize) }}</small><p v-if="order.notes" class="finance-order-notes">{{ order.notes }}</p></td><td>{{ dateTime(order.createdAt) }}</td><td>{{ dateTime(order.updatedAt) }}</td><td>{{ order.updatedBy || order.uploadedBy }}</td>
            <td><div class="table-actions"><button type="button" class="btn--secondary btn--sm" :disabled="busy || !canDownload" @click="downloadOrder(order)">تنزيل</button>
              <template v-if="canWrite"><button type="button" class="btn--secondary btn--sm" :disabled="busy" @click="editOrder(order)">تعديل</button><label class="btn btn--secondary btn--sm finance-replace" :class="{ 'is-disabled': busy }"><span>استبدال الملف</span><input type="file" :accept="allowed" :disabled="busy" :aria-label="`استبدال ${order.fileName}`" @change="replaceFile(order, $event)" /></label><button type="button" class="btn--danger btn--sm" :disabled="busy" @click="pendingRemoval = order; editingOrder = null">إزالة</button></template>
            </div><div v-if="pendingRemoval?.id === order.id" class="finance-removal" role="alert"><p>إزالة هذا الأمر من الاتفاقية؟</p><div class="table-actions"><button type="button" class="btn--danger btn--sm" :disabled="busy" @click="removeOrder">تأكيد الإزالة</button><button type="button" class="btn--secondary btn--sm" :disabled="busy" @click="pendingRemoval = null">إلغاء</button></div></div></td>
          </tr><tr v-if="canWrite && editingOrder === order.id"><td colspan="5"><form class="finance-order-edit" @submit.prevent="saveOrderMetadata"><label class="form-field"><span>اسم أمر الصرف</span><input v-model="editForm.title" required maxlength="255" :disabled="busy" /></label><label class="form-field"><span>ملاحظات</span><textarea v-model="editForm.notes" rows="2" maxlength="2000" :disabled="busy"></textarea></label><div class="table-actions"><button type="submit" :disabled="busy || !editForm.title.trim()">حفظ التعديلات</button><button type="button" class="btn--secondary" :disabled="busy" @click="editingOrder = null">إلغاء</button></div></form></td></tr></template>
        </tbody>
      </table></div>
    </section>
  </main>
</template>

<style scoped>
.finance-agreements { min-width: 36rem; }
.finance-agreement-row { cursor: pointer; }
.finance-agreement-row:focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: -2px; }
.finance-agreements .finance-agreement-row--selected > td { background: var(--color-primary-50); }
.finance-agreements .finance-agreement-row--selected > td:first-child { box-shadow: inset -3px 0 var(--color-primary-600); }
.finance-orders-panel { scroll-margin-block-start: 1rem; }
.finance-orders-heading { align-items: flex-start; flex-wrap: wrap; padding-block-end: 1rem; border-bottom: 1px solid var(--color-border); }
.finance-orders-heading > div { flex: 1 1 16rem; min-width: 0; }
.finance-document-selector { flex: 1 1 20rem; max-width: 32rem; min-width: 0; }
.finance-selected-document { margin: 0.5rem 0 0; color: var(--color-text-muted); line-height: 1.7; }
.finance-order-notes { margin: 0.5rem 0 0; white-space: pre-wrap; font-size: 0.85rem; }
.finance-order-edit { display: grid; gap: 1rem; padding: 0.5rem; }
.finance-category { display: block; margin-block-start: 0.3rem; color: var(--color-text-muted); font-size: 0.8rem; font-weight: 400; }
.finance-agreement-summary { max-width: 32rem; margin: 0 0 0.6rem; white-space: normal; overflow-wrap: anywhere; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.finance-pagination { display: flex; justify-content: flex-end; align-items: center; gap: 1rem; margin-block-start: 1rem; }
.finance-upload { display: grid; gap: 1rem; padding: 1rem; margin-block-end: 1.5rem; background: var(--color-muted-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.finance-upload h3 { margin: 0; }
.finance-upload > button { justify-self: start; }
.picked-files { margin: 0; padding-inline-start: 1.25rem; overflow-wrap: anywhere; font-size: 0.85rem; line-height: 1.8; }
.finance-orders { min-width: 45rem; }
.finance-file-name { min-width: 12rem; max-width: 20rem; white-space: normal; overflow-wrap: anywhere; }
.finance-replace { position: relative; overflow: hidden; cursor: pointer; }
.finance-replace input { position: absolute; inset: 0; width: 100%; opacity: 0; cursor: pointer; }
.finance-replace:focus-within { box-shadow: var(--focus-ring); }
.finance-replace.is-disabled { opacity: 0.55; cursor: not-allowed; }
.finance-removal { padding: 0.75rem; margin-block-start: 0.75rem; border: 1px solid var(--color-danger); border-radius: var(--radius-md); background: var(--color-danger-bg); }
.finance-removal p { margin-block-end: 0.5rem; white-space: normal; }
</style>
