<script setup>
import PlanningCostModal from '@/presentation/components/PlanningCostModal.vue'
import { costText, hasCostTable, workDetails } from '@/presentation/utils/agreementCosts'
import AgreementAttachmentDownload from '@/presentation/components/AgreementAttachmentDownload.vue'
import { getAccessToken } from '@/core/api/authSession'

import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import container from '@/di/container'
import { apiRequest } from '@/core/api/apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import { CONTRACT_TYPES } from '@/presentation/config/contracts'
import { contractPhase, formatContractDate } from '@/presentation/utils/contractDates'
import PageHeader from '@/presentation/components/PageHeader.vue'
import BaseModal from '@/presentation/components/BaseModal.vue'
import AgreementOrdersModal from '@/presentation/components/AgreementOrdersModal.vue'

const props = defineProps({ feature: { type: String, required: true } })
const route = useRoute()
const forms = {
  'doctoral-contracts': defineAsyncComponent(() => import('./DoctoralContractForm.vue')),
  'nafath-centers': defineAsyncComponent(() => import('./NafathCentersView.vue')),
  'lifelong-learning': defineAsyncComponent(() => import('./LifelongLearningView.vue')),
  'educational-content': defineAsyncComponent(() => import('./EducationalContentView.vue')),
  'other-agreements': defineAsyncComponent(() => import('./OtherAgreementsView.vue')),
  memorandum: defineAsyncComponent(() => import('./OtherAgreementsView.vue')),
}
const isDoctoral = computed(() => props.feature === 'doctoral-contracts')
const isPlanning = computed(() => props.feature === 'planning')
const availableTypes = computed(() => CONTRACT_TYPES.filter(type =>
  isPlanning.value || (container.authRepository.hasPermission(type.feature, 'read') && type.feature === props.feature)))
const title = computed(() => isPlanning.value ? 'التخطيط والمتابعة' : availableTypes.value[0]?.title || 'الاتفاقيات')
const selectedType = ref(CONTRACT_TYPES.some(type => type.feature === route.query.type) ? route.query.type : '')
const activeType = computed(() => isPlanning.value ? selectedType.value : props.feature)
const canAdd = computed(() => activeType.value && container.authRepository.hasPermission(activeType.value, 'write'))
const records = ref([])
const loading = ref(false)
const error = ref('')
const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const phase = ref(['current', 'future', 'finish'].includes(route.query.phase) ? route.query.phase : '')
const budget = ref('')
const startFrom = ref('')
const endTo = ref('')
const page = ref(1)
const pageSize = 15
const createOpen = ref(false)
const saving = ref(false)
const selected = ref(null)
const orderSelected = ref(null)
const costSelected = ref(null)
const financeOrders = ref('')
const phaseLabels = { current: 'حالية', finish: 'منتهية', future: 'مستقبلية' }

async function load() {
  loading.value = true
  error.value = ''
  const token = getAccessToken()
  if (isPlanning.value) {
    try {
      const response = await apiRequest(API_URLS.planning.list, { headers: { Authorization: `Token ${token}` } })
      records.value = response.data.filter(record => !record.isHidden)
    } catch (e) {
      records.value = []
      error.value = e.message
    } finally {
      loading.value = false
    }
    return
  }
  const results = await Promise.allSettled(availableTypes.value.map(async type => {
    const response = await apiRequest(type.endpoint, { headers: { Authorization: `Token ${token}` } })
    return response.data.map(record => ({ ...record, feature: type.feature, category: type.title, key: `${type.feature}-${record.id}` }))
  }))
  records.value = results.flatMap(result => result.status === 'fulfilled' ? result.value : [])
  const failures = results.flatMap((result, index) => result.status === 'rejected'
    ? [`${availableTypes.value[index].title}: ${result.reason.message}`] : [])
  error.value = failures.join(' • ')
  loading.value = false
}

const filtered = computed(() => records.value.filter(record => {
  const text = `${record.agreementNumber} ${record.name} ${record.companyName || ''} ${record.doctorRank || ''} ${record.tasks || ''} ${record.commencementOrder || ''}`.toLowerCase()
  return (!isPlanning.value || !record.isHidden) &&
    (!activeType.value || record.feature === activeType.value) &&
    (!query.value.trim() || text.includes(query.value.trim().toLowerCase())) &&
    (!phase.value || contractPhase(record) === phase.value) &&
    (!budget.value || record.budgetType === budget.value) &&
    (!financeOrders.value || (Number(record.orderCount) > 0) === (financeOrders.value === 'with')) &&
    (!startFrom.value || (record.startDate && record.startDate >= startFrom.value)) &&
    (!endTo.value || (record.endDate && record.endDate <= endTo.value))
}))
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
watch(totalPages, total => { page.value = Math.min(page.value, total) })
const pageRows = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch([query, phase, budget, startFrom, endTo, selectedType, financeOrders], () => { page.value = 1 })

function clearFilters() {
  query.value = phase.value = budget.value = startFrom.value = endTo.value = financeOrders.value = ''
  page.value = 1
}
function exportResults() {
  const cells = value => {
    const text = String(value ?? '')
    const safe = /^[=+@\-\t\r]/.test(text) ? `'${text}` : text
    return `"${safe.replaceAll('"', '""')}"`
  }
  const rows = isDoctoral.value ? [doctoralFields.map(([, label]) => label), ...filtered.value.map(record => doctoralFields.map(([key]) => record[key]))] : [
    ['رقم الاتفاقية', 'اسم الاتفاقية', 'نوع الاتفاقية', 'تاريخ البدء', 'تاريخ الانتهاء', 'تاريخ التذكير', 'عدد أوامر الصرف', ...(isPlanning.value ? ['تفاصيل العمل', 'حالة الاتفاقية', 'التكلفة', 'تفاصيل التكلفة'] : [])],
    ...filtered.value.map(record => [record.agreementNumber, record.name, record.category, record.startDate, record.endDate, record.reminderDate, record.orderCount || 0,
      ...(isPlanning.value ? [workDetails(record), record.status || phaseLabels[contractPhase(record)] || '', hasCostTable(record) ? JSON.stringify(record.costTable?.length ? record.costTable : record.paymentSchedule || []) : costText(record), record.paymentText || ''] : [])]),
  ]
  const file = new Blob(['\uFEFF', rows.map(row => row.map(cells).join(',')).join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.download = 'الاتفاقيات.csv'
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 0)
}
function openCreate() { if (canAdd.value) createOpen.value = true }
function updateOrderCount({ key, count }) {
  const record = records.value.find(item => item.key === key)
  if (record) record.orderCount = count
}
async function onSaved() {
  createOpen.value = false
  saving.value = false
  clearFilters()
  await load()
}
const doctoralFields = [['contractNumber', 'رقم العقد'], ['doctorName', 'اسم الدكتور'], ['tasks', 'المهام'], ['doctorRank', 'رتبة الدكتور'], ['duration', 'مدة العقد'], ['commencementOrder', 'أمر المباشرة']]
const standardDetailFields = [
  ['agreementNumber', 'رقم الاتفاقية'], ['name', 'اسم الاتفاقية'], ['companyName', 'الجهة المتعاقدة'],
  ['subject', 'الموضوع'], ['status', 'الحالة المسجلة'], ['estimatedCost', 'الكلفة التقديرية'],
  ['additionalCourses', 'المقررات الإضافية'], ['quarterlyDue', 'المبلغ الفصلي'],
  ['paymentText', 'تفاصيل الدفع'], ['disbursement', 'الصرف'], ['contractText', 'نص العقد'],
]
const detailFields = computed(() => selected.value?.feature === 'doctoral-contracts' ? doctoralFields : standardDetailFields)
onMounted(load)
</script>

<template>
  <main class="app-page contract-list" dir="rtl">
    <PageHeader :title="title" eyebrow="إدارة العقود والاتفاقيات" :description="isPlanning ? 'الاتفاقيات غير المخفية عن التخطيط، مع تصنيف الحالة تلقائياً حسب تاريخ البداية والنهاية.' : isDoctoral ? 'استعرض عقود الدكتوراه وابحث باسم الدكتور أو رقم العقد أو مهامه.' : 'استعرض الاتفاقيات المحفوظة وابحث فيها، أو أضف اتفاقية جديدة.'">
      <template #actions><button v-if="canAdd" type="button" @click="openCreate">{{ isDoctoral ? 'إضافة عقد' : 'إضافة اتفاقية' }}</button></template>
    </PageHeader>
    <section class="panel">
      <div class="contract-filters">
        <label v-if="isPlanning" class="form-field"><span>نوع الاتفاقية</span>
          <select v-model="selectedType"><option value="">جميع الاتفاقيات</option><option v-for="type in availableTypes" :key="type.feature" :value="type.feature">{{ type.title }}</option></select>
        </label>
        <label class="form-field"><span>البحث</span><input v-model="query" type="search" :placeholder="isDoctoral ? 'رقم العقد، اسم الدكتور، الرتبة أو المهام' : 'رقم الاتفاقية، الاسم أو الجهة'" /></label>
        <label v-if="!isDoctoral" class="form-field"><span>الحالة حسب التاريخ</span><select v-model="phase"><option value="">الكل</option><option v-for="(label, key) in phaseLabels" :key="key" :value="key">{{ label }}</option></select></label>
        <label class="form-field"><span>أوامر الصرف</span><select v-model="financeOrders"><option value="">الكل</option><option value="with">لديها أوامر صرف</option><option value="without">بدون أوامر صرف</option></select></label>
        <label v-if="!['other-agreements', 'memorandum', 'doctoral-contracts'].includes(activeType)" class="form-field"><span>نوع الموازنة</span><select v-model="budget"><option value="">الكل</option><option value="current">جاري</option><option value="investment">استثماري</option></select></label>
        <label v-if="!isDoctoral" class="form-field"><span>البدء من</span><input v-model="startFrom" type="date" /></label>
        <label v-if="!isDoctoral" class="form-field"><span>الانتهاء حتى</span><input v-model="endTo" type="date" /></label>
      </div>
      <div class="contract-list__toolbar"><span class="result-count" aria-live="polite">{{ isDoctoral ? 'عدد العقود' : 'عدد الاتفاقيات' }}: {{ filtered.length }}</span>
        <div class="table-actions"><button class="btn--secondary btn--sm" type="button" @click="clearFilters">إلغاء الفلاتر</button><button class="btn--secondary btn--sm" type="button" :disabled="loading" @click="load">تحديث</button><button class="btn--secondary btn--sm" type="button" :disabled="loading || !filtered.length" @click="exportResults">تصدير النتائج CSV</button></div>
      </div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <p v-if="isPlanning && !availableTypes.length" class="notice">لا توجد أنواع اتفاقيات متاحة لدورك. اطلب صلاحية القراءة من مسؤول النظام.</p>
      <div class="table-scroll" :aria-busy="loading">
        <table class="contract-list__table">
          <thead><tr><th>{{ isDoctoral ? 'رقم العقد' : 'رقم الاتفاقية' }}</th><th>{{ isDoctoral ? 'اسم الدكتور' : 'اسم الاتفاقية' }}</th><template v-if="isDoctoral"><th>المهام</th><th>رتبة الدكتور</th><th>مدة العقد</th><th>أمر المباشرة</th></template><template v-else><th>تاريخ البدء</th><th>تاريخ الانتهاء</th><th>تاريخ التذكير</th><th>الحالة حسب التاريخ</th></template><template v-if="isPlanning"><th>تفاصيل العمل</th><th>حالة الاتفاقية</th><th>التكلفة</th><th>تفاصيل التكلفة</th><th>نوع الاتفاقية</th></template><th>الإجراءات</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td :colspan="isPlanning ? 12 : 7" class="empty-state">{{ isDoctoral ? 'جارٍ تحميل العقود…' : 'جارٍ تحميل الاتفاقيات…' }}</td></tr>
            <tr v-else-if="!pageRows.length"><td :colspan="isPlanning ? 12 : 7" class="empty-state">{{ isDoctoral ? 'لا توجد عقود تطابق الفلاتر.' : 'لا توجد اتفاقيات تطابق الفلاتر.' }}</td></tr>
            <tr v-for="record in loading ? [] : pageRows" :key="record.key">
              <td>{{ record.agreementNumber || '—' }}</td><td class="contract-list__name">{{ record.name || '—' }}</td>
              <template v-if="isDoctoral"><td class="planning-description">{{ record.tasks }}</td><td>{{ record.doctorRank }}</td><td>{{ record.duration }}</td><td class="planning-description">{{ record.commencementOrder }}</td></template>
              <template v-else><td>{{ formatContractDate(record.startDate) }}</td><td>{{ formatContractDate(record.endDate) }}</td><td>{{ formatContractDate(record.reminderDate) }}</td>
              <td><span class="status-badge" :class="`status-${contractPhase(record)}`">{{ phaseLabels[contractPhase(record)] || '—' }}</span></td></template>
              <template v-if="isPlanning">
                <td class="planning-description">{{ workDetails(record) }}</td>
                <td>{{ record.status || phaseLabels[contractPhase(record)] || '—' }}</td>
                <td class="planning-cost-cell"><button v-if="hasCostTable(record)" type="button" class="btn--secondary btn--sm" @click="costSelected = record">إظهار الجدول</button><span v-else>{{ costText(record) }}</span></td>
                <td class="planning-description">{{ record.paymentText || '—' }}</td>
                <td>{{ record.category }}</td>
              </template>
              <td><div class="table-actions contract-list__actions"><button type="button" class="btn--secondary btn--sm" @click="selected = record">عرض التفاصيل</button><button type="button" class="btn--secondary btn--sm" :disabled="!(record.orderCount > 0)" :title="record.orderCount > 0 ? 'عرض أوامر الصرف المرتبطة بهذه الاتفاقية' : 'لا توجد أوامر صرف لهذه الاتفاقية'" @click="orderSelected = record">عرض أوامر الصرف ({{ record.orderCount || 0 }})</button></div></td>
            </tr>
          </tbody>
        </table>
      </div>
      <nav class="contract-pagination" aria-label="صفحات الاتفاقيات"><button type="button" class="btn--secondary btn--sm" :disabled="page <= 1" @click="page--">السابق</button><span>صفحة {{ page }} من {{ totalPages }}</span><button type="button" class="btn--secondary btn--sm" :disabled="page >= totalPages" @click="page++">التالي</button></nav>
    </section>
    <BaseModal v-model="createOpen" :title="`إضافة ${CONTRACT_TYPES.find(type => type.feature === activeType)?.title || 'اتفاقية'}`" :description="isDoctoral ? 'أدخل بيانات العقد وأرفق الوثيقة. الحقول المعلّمة بنجمة مطلوبة.' : 'أدخل بيانات الاتفاقية حسب الأقسام. الحقول المعلّمة بنجمة مطلوبة.'" size="lg" :busy="saving">
      <component v-if="createOpen" :is="forms[activeType]" :agreement-type="activeType" @saved="onSaved" @busy="saving = $event" />
      <template #footer><button type="button" class="btn--secondary" :disabled="saving" @click="createOpen = false">إلغاء والعودة للقائمة</button></template>
    </BaseModal>
    <BaseModal :model-value="!!selected" :title="selected?.feature === 'doctoral-contracts' ? 'تفاصيل عقد الدكتوراه' : 'تفاصيل الاتفاقية'" size="lg" @update:model-value="selected = null">
      <template v-if="selected">
        <dl class="contract-detail"><template v-for="[key, label] in detailFields" :key="key"><template v-if="selected[key] !== undefined && selected[key] !== '' && selected[key] !== null"><dt>{{ label }}</dt><dd>{{ selected[key] }}</dd></template></template>
          <template v-for="[key, label] in (selected.feature === 'doctoral-contracts' ? [] : [['startDate', 'تاريخ البدء'], ['endDate', 'تاريخ الانتهاء'], ['reminderDate', 'تاريخ التذكير']])" :key="key"><dt>{{ label }}</dt><dd>{{ formatContractDate(selected[key]) }}</dd></template>
        </dl>
        <section v-for="(row, index) in selected.rows || []" :key="index" class="panel"><h3>{{ row.header }}</h3><p class="contract-detail__text">{{ row.body }}</p></section>
        <div v-if="selected.paymentSchedule?.length" class="table-scroll"><table><thead><tr><th>الدفعة</th><th>المبلغ</th><th>تاريخ الاستحقاق</th></tr></thead><tbody><tr v-for="(row, index) in selected.paymentSchedule" :key="index"><td>{{ row.label }}</td><td>{{ row.amount }}</td><td>{{ formatContractDate(row.dueDate) }}</td></tr></tbody></table></div>
        <AgreementAttachmentDownload :agreement="{ ...selected, feature: selected.feature || feature }" :scope="feature === 'planning' ? 'planning' : 'agreement'" />
      </template>
    </BaseModal>
    <PlanningCostModal :agreement="costSelected" @close="costSelected = null" />
    <AgreementOrdersModal :agreement="orderSelected" :scope="isPlanning ? 'planning' : 'agreement'" @close="orderSelected = null" @loaded="updateOrderCount" />
  </main>
</template>

<style scoped>
.contract-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 10rem), 1fr)); gap: 1rem; }
.contract-list__toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-block: 1.25rem; }
.result-count { margin: 0; }
.contract-list__table { min-width: 850px; }
.planning-description { min-width: 15rem; max-width: 25rem; white-space: pre-wrap; overflow-wrap: anywhere; }
.planning-cost-cell { min-width: 10rem; max-width: 20rem; white-space: pre-wrap; overflow-wrap: anywhere; }
.contract-list__name { white-space: normal; min-width: 12rem; }
.contract-list__actions { min-width: 21rem; }
.contract-pagination { display: flex; align-items: center; justify-content: flex-end; gap: 1rem; margin-block-start: 1rem; font-size: 0.9rem; }
.contract-detail { display: grid; grid-template-columns: minmax(7rem, 1fr) 3fr; gap: 0; margin: 0 0 1rem; }
.contract-detail dt, .contract-detail dd { margin: 0; padding: 0.8rem; border-bottom: 1px solid var(--color-border); overflow-wrap: anywhere; white-space: pre-wrap; }
.contract-detail dt { font-weight: 700; background: var(--color-muted-surface); }
.contract-detail__text { white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 640px) {
  .contract-detail { grid-template-columns: 1fr; }
  .contract-detail dt { border-bottom: 0; padding-block-end: 0.35rem; }
  .contract-detail dd { padding-block-start: 0.35rem; }
}
</style>
