<script setup>
import AgreementAttachmentDownload from '@/presentation/components/AgreementAttachmentDownload.vue'
import { downloadDocument } from '@/core/api/fileDownloads'
import { getAccessToken } from '@/core/api/authSession'

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { API_URLS } from '@/core/config/apiUrls'
import { apiRequest } from '@/core/api/apiClient'
import { CONTRACT_TYPES } from '@/presentation/config/contracts'
import { formatContractDate } from '@/presentation/utils/contractDates'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
import { useNotifications } from '@/presentation/composables/useNotifications'
import PageHeader from '@/presentation/components/PageHeader.vue'
import AgreementOrdersModal from '@/presentation/components/AgreementOrdersModal.vue'

const { canWrite, canDownload } = useFeatureAccess('dean')
const route = useRoute()
const notify = useNotifications()
const agreements = ref([])
const loading = ref(false)
const error = ref('')
const query = ref('')
const kind = ref(CONTRACT_TYPES.some(type => type.feature === route.query.type) ? route.query.type : '')
const visibility = ref('')
const financeOrders = ref('')
const orderSelected = ref(null)
const page = ref(1)
const pageSize = 15
const selectedKey = ref('')
const detail = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const reviewPanel = ref(null)
const savingKey = ref('')
const downloading = ref(null)
let detailRequest = 0
const headers = () => ({ Authorization: `Token ${getAccessToken()}` })
const selected = computed(() => agreements.value.find(item => item.key === selectedKey.value))
const filtered = computed(() => agreements.value.filter(item =>
  (!kind.value || item.feature === kind.value) &&
  (visibility.value === '' || item.isHidden === (visibility.value === 'hidden')) &&
  (!financeOrders.value || (item.orderCount > 0) === (financeOrders.value === 'with')) &&
  `${item.name} ${item.agreementNumber} ${item.details || ''}`.toLowerCase().includes(query.value.trim().toLowerCase())))
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const rows = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch([query, kind, visibility, financeOrders], () => { page.value = 1 })
watch(pages, total => { page.value = Math.min(page.value, total) })
const fields = [
  ['agreementNumber', 'رقم الاتفاقية'], ['name', 'اسم الاتفاقية'], ['companyName', 'الجهة المتعاقدة'],
  ['subject', 'الموضوع'], ['status', 'الحالة المسجلة'], ['estimatedCost', 'الكلفة التقديرية'],
  ['additionalCourses', 'المقررات الإضافية'], ['quarterlyDue', 'المبلغ المستحق الفصلي'],
  ['paymentText', 'تفاصيل الدفع'], ['disbursement', 'الصرف'], ['contractText', 'نص العقد'],
]

async function load() {
  if (savingKey.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiRequest(API_URLS.dean.agreements, { headers: headers() })
    agreements.value = response.data
    if (selectedKey.value) {
      if (selected.value) await loadDetail(selected.value)
      else clearSelection()
    }
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

async function loadDetail(agreement) {
  if (savingKey.value) return
  const requestId = ++detailRequest
  detailLoading.value = true
  detail.value = null
  detailError.value = ''
  try {
    const response = await apiRequest(API_URLS.dean.agreement(agreement.feature, agreement.id), { headers: headers() })
    if (requestId !== detailRequest || selectedKey.value !== agreement.key) return
    detail.value = response.data
    agreement.orderCount = response.data.orderCount
    agreement.isHidden = response.data.isHidden
  } catch (e) { if (requestId === detailRequest) detailError.value = e.message }
  finally { if (requestId === detailRequest) detailLoading.value = false }
}

async function selectAgreement(agreement) {
  if (savingKey.value || loading.value) return
  selectedKey.value = agreement.key
  const request = loadDetail(agreement)
  await nextTick()
  reviewPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  await request
}

function changeAgreement(key) {
  const agreement = agreements.value.find(item => item.key === key)
  if (agreement) selectAgreement(agreement)
  else clearSelection()
}

function clearSelection() {
  if (savingKey.value) return
  selectedKey.value = ''
  detail.value = null
  detailError.value = ''
  detailLoading.value = false
  detailRequest++
}

async function setPlanningVisibility(agreement, visible, event) {
  if (event) event.target.checked = !agreement.isHidden
  if (!canWrite.value || savingKey.value || loading.value || detailLoading.value || visible === !agreement.isHidden) return
  savingKey.value = agreement.key
  error.value = ''
  try {
    const response = await apiRequest(API_URLS.dean.visibility(agreement.feature, agreement.id), {
      method: 'PATCH', headers: headers(), body: JSON.stringify({ isHidden: !visible }),
    })
    agreement.isHidden = response.data.isHidden
    if (detail.value?.key === agreement.key) detail.value.isHidden = response.data.isHidden
    notify.success(agreement.isHidden ? 'تم إخفاء الاتفاقية عن التخطيط' : 'أصبحت الاتفاقية ظاهرة في التخطيط')
  } catch (e) { error.value = e.message; notify.error(e.message) }
  finally { savingKey.value = ''; if (event) event.target.checked = !agreement.isHidden }
}

async function downloadOrder(order) {
  if (!selected.value || downloading.value !== null) return
  const agreement = selected.value
  downloading.value = order.id
  detailError.value = ''
  try {
    await downloadDocument({ ...agreement, scope: 'dean', orderId: order.id, fileName: order.fileName })
  } catch (e) { if (selectedKey.value === agreement.key) detailError.value = e.message }
  finally { downloading.value = null }
}

function dateTime(value) {
  return new Intl.DateTimeFormat('ar-SY-u-ca-gregory', { timeZone: 'Asia/Damascus', dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}
function updateOrderCount({ key, count }) {
  const agreement = agreements.value.find(item => item.key === key)
  if (agreement) agreement.orderCount = count
}
onMounted(async () => {
  await load()
  const agreement = agreements.value.find(item => item.key === route.query.document)
  if (agreement) await selectAgreement(agreement)
})
onBeforeUnmount(() => { detailRequest++ })
</script>

<template>
  <main class="app-page dean-page" dir="rtl">
    <PageHeader title="العميد ومراجعة الاتفاقيات" eyebrow="العقود وأوامر الصرف" description="جميع العقود والاتفاقيات، بما فيها المخفية عن التخطيط. اختر اتفاقية لمراجعة تفاصيلها وأوامر الصرف المرتبطة بها.">
      <template #actions><button type="button" class="btn--secondary" :disabled="loading || !!savingKey" @click="load">تحديث</button></template>
    </PageHeader>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <section class="panel">
      <div class="dean-filters">
        <label class="form-field"><span>البحث</span><input v-model="query" type="search" placeholder="اسم الاتفاقية، الرقم أو التفاصيل" /></label>
        <label class="form-field"><span>نوع الاتفاقية</span><select v-model="kind"><option value="">جميع الأنواع</option><option v-for="type in CONTRACT_TYPES" :key="type.feature" :value="type.feature">{{ type.title }}</option></select></label>
        <label class="form-field"><span>الظهور في التخطيط</span><select v-model="visibility"><option value="">الكل</option><option value="visible">ظاهرة في التخطيط</option><option value="hidden">مخفية عن التخطيط</option></select></label>
        <label class="form-field"><span>أوامر الصرف</span><select v-model="financeOrders"><option value="">الكل</option><option value="with">لديها أوامر صرف</option><option value="without">بدون أوامر صرف</option></select></label>
        <button type="button" class="btn--secondary" @click="query = ''; kind = ''; visibility = ''; financeOrders = ''">إلغاء الفلاتر</button>
      </div>
      <p class="result-count" aria-live="polite">عدد العقود والاتفاقيات: {{ filtered.length }}</p>
      <div class="table-scroll" :aria-busy="loading"><table class="dean-agreements"><thead><tr><th>اسم العقد / الاتفاقية</th><th>الرقم</th><th>التفاصيل</th><th>أوامر الصرف</th><th>الظهور في التخطيط</th></tr></thead>
        <tbody><tr v-if="loading"><td colspan="5" class="empty-state">جارٍ تحميل الاتفاقيات…</td></tr><tr v-else-if="!rows.length"><td colspan="5" class="empty-state">لا توجد اتفاقيات تطابق الفلاتر.</td></tr>
          <tr v-for="agreement in loading ? [] : rows" :key="agreement.key" class="dean-agreement-row" :class="{ 'is-selected': selectedKey === agreement.key }" :tabindex="savingKey ? -1 : 0" :aria-selected="selectedKey === agreement.key" @click="selectAgreement(agreement)" @keydown.enter.self="selectAgreement(agreement)" @keydown.space.self.prevent="selectAgreement(agreement)">
            <td><strong>{{ agreement.name || '—' }}</strong><small class="dean-meta">{{ agreement.category }}</small></td><td>{{ agreement.agreementNumber || '—' }}</td>
            <td><p class="dean-summary">{{ agreement.details || '—' }}</p><button type="button" class="btn--secondary btn--sm" :disabled="!!savingKey" aria-controls="dean-review" @click.stop="selectAgreement(agreement)">عرض التفاصيل</button></td>
            <td><button type="button" class="btn--secondary btn--sm" :disabled="!!savingKey || !(agreement.orderCount > 0)" @click.stop="orderSelected = agreement">عرض أوامر الصرف ({{ agreement.orderCount }})</button></td>
            <td @click.stop><label class="dean-visibility"><input type="checkbox" role="switch" :checked="!agreement.isHidden" :disabled="!canWrite || !!savingKey || loading || detailLoading" :aria-label="`إظهار ${agreement.name} في التخطيط`" @change="setPlanningVisibility(agreement, $event.target.checked, $event)" /><span>{{ savingKey === agreement.key ? 'جارٍ الحفظ…' : agreement.isHidden ? 'مخفية عن التخطيط' : 'ظاهرة في التخطيط' }}</span></label></td>
          </tr>
        </tbody>
      </table></div>
      <nav class="dean-pagination" aria-label="صفحات اتفاقيات العميد"><button type="button" class="btn--secondary btn--sm" :disabled="page <= 1" @click="page--">السابق</button><span>صفحة {{ page }} من {{ pages }}</span><button type="button" class="btn--secondary btn--sm" :disabled="page >= pages" @click="page++">التالي</button></nav>
    </section>

    <section id="dean-review" ref="reviewPanel" class="panel dean-review" aria-labelledby="dean-review-title" :aria-busy="detailLoading">
      <header class="panel-heading dean-review-heading">
        <div><h2 id="dean-review-title">مراجعة الاتفاقية وأوامر الصرف</h2><p class="dean-meta">{{ selected ? `${selected.name} — ${selected.agreementNumber}` : 'اختر اتفاقية من الجدول أو القائمة لعرض تفاصيلها.' }}</p></div>
        <label class="form-field dean-selector"><span>العقد / الاتفاقية</span><select :value="selectedKey" :disabled="!!savingKey || loading" @change="changeAgreement($event.target.value)"><option value="">اختر اتفاقية</option><option v-for="agreement in agreements" :key="agreement.key" :value="agreement.key">{{ agreement.name }} — {{ agreement.agreementNumber }} ({{ agreement.category }})</option></select></label>
      </header>
      <p v-if="!selected" class="empty-state">لم يتم تحديد اتفاقية.</p>
      <p v-else-if="detailLoading" class="empty-state">جارٍ تحميل تفاصيل الاتفاقية وأوامر الصرف…</p>
      <p v-if="detailError" class="error" role="alert">{{ detailError }}</p>
      <button v-if="selected && detailError && !detailLoading" type="button" class="btn--secondary" @click="loadDetail(selected)">إعادة المحاولة</button>
      <template v-if="detail && !detailLoading">
        <div class="dean-visibility-summary"><span :class="['status-badge', selected.isHidden ? 'status-badge--warning' : 'status-badge--success']">{{ selected.isHidden ? 'مخفية عن التخطيط' : 'ظاهرة في التخطيط' }}</span><button v-if="canWrite" type="button" class="btn--secondary" :disabled="!!savingKey || loading" @click="setPlanningVisibility(selected, selected.isHidden)">{{ selected.isHidden ? 'إظهار الاتفاقية في التخطيط' : 'إخفاء الاتفاقية عن التخطيط' }}</button></div>
        <dl class="dean-details"><template v-for="[key, label] in fields" :key="key"><template v-if="detail[key] !== undefined && detail[key] !== '' && detail[key] !== null"><dt>{{ label }}</dt><dd>{{ detail[key] }}</dd></template></template>
          <template v-for="[key, label] in [['startDate', 'تاريخ البدء'], ['endDate', 'تاريخ الانتهاء'], ['reminderDate', 'تاريخ التذكير']]" :key="key"><dt>{{ label }}</dt><dd>{{ formatContractDate(detail[key]) }}</dd></template>
          <template v-if="detail.budgetType"><dt>نوع الموازنة</dt><dd>{{ detail.budgetType === 'investment' ? 'استثماري' : 'جاري' }}</dd></template>
        </dl>
        <section v-for="(row, index) in detail.rows || []" :key="index" class="dean-clause"><h3>{{ row.header || `بند ${index + 1}` }}</h3><p>{{ row.body }}</p></section>
        <div v-if="detail.paymentSchedule?.length" class="table-scroll dean-schedule"><table><thead><tr><th>الدفعة</th><th>المبلغ</th><th>تاريخ الاستحقاق</th></tr></thead><tbody><tr v-for="(row, index) in detail.paymentSchedule" :key="index"><td>{{ row.label }}</td><td>{{ row.amount }}</td><td>{{ formatContractDate(row.dueDate) }}</td></tr></tbody></table></div>
        <AgreementAttachmentDownload :agreement="{ ...detail, feature: selected.feature }" scope="dean" />
        <div class="panel-heading dean-orders-heading"><h3>أوامر الصرف ({{ detail.orders.length }})</h3><button type="button" class="btn--secondary btn--sm" :disabled="!!savingKey" @click="loadDetail(selected)">تحديث أوامر الصرف</button></div>
        <div class="table-scroll"><table class="dean-orders"><thead><tr><th>أمر الصرف</th><th>الملف</th><th>تاريخ الرفع</th><th>آخر تحديث</th><th>بواسطة</th><th>الإجراءات</th></tr></thead><tbody>
          <tr v-if="!detail.orders.length"><td colspan="6" class="empty-state">لم تُرفع أوامر صرف لهذه الاتفاقية بعد.</td></tr>
          <tr v-for="order in detail.orders" :key="order.id"><td><strong>{{ order.title || order.fileName }}</strong><p v-if="order.notes" class="dean-order-notes">{{ order.notes }}</p></td><td class="dean-file-name">{{ order.fileName }}</td><td>{{ dateTime(order.createdAt) }}</td><td>{{ dateTime(order.updatedAt) }}</td><td>{{ order.updatedBy || order.uploadedBy }}</td><td><button type="button" class="btn--secondary btn--sm" :disabled="downloading !== null || !canDownload" @click="downloadOrder(order)">{{ downloading === order.id ? 'جارٍ التنزيل…' : 'تنزيل' }}</button></td></tr>
        </tbody></table></div>
      </template>
    </section>
    <AgreementOrdersModal :agreement="orderSelected" scope="dean" @close="orderSelected = null" @loaded="updateOrderCount" />
  </main>
</template>

<style scoped>
.dean-filters { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)) auto; align-items: end; gap: 1rem; margin-block-end: 1.25rem; }
.dean-agreements { min-width: 58rem; }
.dean-agreement-row { cursor: pointer; }
.dean-agreement-row:focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: -2px; }
.dean-agreements .is-selected > td { background: var(--color-primary-50); }
.dean-meta { display: block; margin: 0.4rem 0 0; color: var(--color-text-muted); font-size: 0.85rem; line-height: 1.7; }
.dean-summary { max-width: 24rem; white-space: normal; overflow-wrap: anywhere; margin: 0 0 0.5rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.dean-visibility { display: flex; align-items: center; gap: 0.6rem; cursor: pointer; white-space: nowrap; }
.dean-visibility input { width: 1.1rem; height: 1.1rem; }
.dean-pagination { display: flex; justify-content: flex-end; align-items: center; gap: 1rem; margin-block-start: 1rem; }
.dean-review { scroll-margin-block-start: 1rem; }
.dean-review-heading { flex-wrap: wrap; align-items: start; padding-block-end: 1rem; border-bottom: 1px solid var(--color-border); }
.dean-review-heading > div { flex: 1 1 16rem; min-width: 0; }
.dean-selector { flex: 1 1 20rem; max-width: 32rem; min-width: 0; }
.dean-visibility-summary { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin-block-end: 1rem; }
.dean-details { display: grid; grid-template-columns: minmax(9rem, 1fr) 3fr; margin: 0 0 1.5rem; }
.dean-details dt, .dean-details dd { padding: 0.8rem; margin: 0; border-bottom: 1px solid var(--color-border); white-space: pre-wrap; overflow-wrap: anywhere; min-width: 0; }
.dean-details dt { font-weight: 700; background: var(--color-muted-surface); }
.dean-clause { padding: 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); margin-block-end: 1rem; }
.dean-clause p, .dean-order-notes { white-space: pre-wrap; overflow-wrap: anywhere; margin: 0.5rem 0 0; }
.dean-schedule { margin-block-end: 1rem; }
.dean-orders-heading { margin-block-start: 1.5rem; flex-wrap: wrap; }
.dean-orders-heading h3 { margin: 0; }
.dean-orders { min-width: 52rem; }
.dean-orders td:first-child, .dean-file-name { max-width: 20rem; min-width: 10rem; white-space: normal; overflow-wrap: anywhere; }
@media (max-width: 800px) { .dean-filters { grid-template-columns: 1fr 1fr; } }
@media (max-width: 520px) { .dean-filters { grid-template-columns: 1fr; } .dean-details { grid-template-columns: 1fr; } .dean-details dd { margin-block-end: 0.6rem; } }
</style>
