<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { apiRequest } from '@/core/api/apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import { formatContractDate } from '@/presentation/utils/contractDates'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
import { useNotifications } from '@/presentation/composables/useNotifications'
import PageHeader from '@/presentation/components/PageHeader.vue'
import BaseModal from '@/presentation/components/BaseModal.vue'
import StatusBadge from '@/presentation/components/StatusBadge.vue'
import ContractRequestForm from './ContractRequestForm.vue'
const { canWrite } = useFeatureAccess('contract-requests')
const notify = useNotifications()
const records = ref([]), loading = ref(false), error = ref(''), query = ref(''), status = ref(''), page = ref(1)
const editorOpen = ref(false), editing = ref(null), selected = ref(null), removal = ref(null), busy = ref(false)
const statusText = value => value === 'success' ? 'تمت المناقصة بنجاح' : 'فشلت المناقصة'
const filtered = computed(() => records.value.filter(record => (!status.value || record.status === status.value) &&
  [record.justificationMemo, record.technicalSpecs, record.legalSpecs, ...record.bids.flatMap(row => [row.number, row.subject])].join(' ').toLowerCase().includes(query.value.trim().toLowerCase())))
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / 15)))
const rows = computed(() => filtered.value.slice((page.value - 1) * 15, page.value * 15))
watch([query, status], () => { page.value = 1 })
watch(pages, value => { page.value = Math.min(page.value, value) })
async function load() {
  loading.value = true; error.value = ''
  try { records.value = (await apiRequest(API_URLS.contractRequests.list)).data }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
}
function openEditor(record = null) { if (canWrite.value) { editing.value = record; editorOpen.value = true } }
async function saved(response) { editorOpen.value = false; notify.success(response.message); await load() }
async function remove() {
  if (!removal.value || busy.value || !canWrite.value) return
  busy.value = true; error.value = ''
  try { const response = await apiRequest(API_URLS.contractRequests.byId(removal.value.id), { method: 'DELETE' }); removal.value = null; notify.success(response.message); await load() }
  catch (e) { error.value = e.message }
  finally { busy.value = false }
}
onMounted(load)
</script>
<template>
  <main class="app-page" dir="rtl">
    <PageHeader title="إضافة عقد" eyebrow="العقود والمناقصات" description="إدارة المذكرة التبريرية ودفاتر الشروط ومحاضر فض العروض والرغبات وحالة المناقصة.">
      <template #actions><button v-if="canWrite" type="button" @click="openEditor()">إضافة عقد جديد</button></template>
    </PageHeader>
    <section class="panel">
      <div class="request-filters"><label class="form-field"><span>البحث</span><input v-model="query" type="search" placeholder="المذكرة أو دفتر الشروط أو رقم المحضر" /></label><label class="form-field"><span>حالة المناقصة</span><select v-model="status"><option value="">الكل</option><option value="success">تمت المناقصة بنجاح</option><option value="failed">فشلت المناقصة</option></select></label></div>
      <div class="panel-heading"><span aria-live="polite">عدد العقود: {{ filtered.length }}</span><div class="table-actions"><button type="button" class="btn--secondary btn--sm" @click="query = ''; status = ''">إلغاء الفلاتر</button><button type="button" class="btn--secondary btn--sm" :disabled="loading" @click="load">تحديث</button></div></div>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div class="table-scroll" :aria-busy="loading"><table class="requests-table"><thead><tr><th>الرقم</th><th>المذكرة التبريرية</th><th>بداية الإعلان</th><th>نهاية الإعلان</th><th>تاريخ التذكير</th><th>الحالة</th><th>المحاضر</th><th>الرغبات</th><th>الإجراءات</th></tr></thead><tbody>
        <tr v-if="loading"><td colspan="9" class="empty-state">جارٍ تحميل العقود…</td></tr><tr v-else-if="!rows.length"><td colspan="9" class="empty-state">لا توجد عقود تطابق الفلاتر.</td></tr>
        <tr v-for="record in loading ? [] : rows" :key="record.id"><td>{{ record.id }}</td><td class="request-summary">{{ record.justificationMemo }}</td><td>{{ formatContractDate(record.announceStart) }}</td><td>{{ formatContractDate(record.announceEnd) }}</td><td>{{ formatContractDate(record.reminderDate) }}</td><td><StatusBadge :tone="record.status === 'success' ? 'success' : 'danger'">{{ statusText(record.status) }}</StatusBadge></td><td>{{ record.bids.length }}</td><td>{{ record.wishes.length }}</td><td><div class="table-actions"><button type="button" class="btn--secondary btn--sm" @click="selected = record">عرض التفاصيل</button><template v-if="canWrite"><button type="button" class="btn--secondary btn--sm" @click="openEditor(record)">تعديل</button><button type="button" class="btn--danger btn--sm" @click="error = ''; removal = record">حذف</button></template></div></td></tr>
      </tbody></table></div>
      <nav class="request-pagination" aria-label="صفحات العقود"><button type="button" class="btn--secondary btn--sm" :disabled="page <= 1" @click="page--">السابق</button><span>صفحة {{ page }} من {{ pages }}</span><button type="button" class="btn--secondary btn--sm" :disabled="page >= pages" @click="page++">التالي</button></nav>
    </section>
    <BaseModal v-model="editorOpen" :title="editing ? 'تعديل العقد' : 'إضافة عقد جديد'" description="الحقول المعلّمة بنجمة مطلوبة. أضف المحاضر والرغبات عند الحاجة." size="lg" :busy="busy">
      <ContractRequestForm v-if="editorOpen" :initial-value="editing" @saved="saved" @busy="busy = $event" />
      <template #footer><button type="button" class="btn--secondary" :disabled="busy" @click="editorOpen = false">إلغاء والعودة للقائمة</button></template>
    </BaseModal>
    <BaseModal :model-value="!!selected" title="تفاصيل العقد" size="lg" @update:model-value="selected = null">
      <template v-if="selected"><dl class="request-detail"><template v-for="[key, label] in [['justificationMemo', 'مذكرة تبريرية'], ['technicalSpecs', 'دفتر شروط فني'], ['legalSpecs', 'دفتر شروط حقوقي']]" :key="key"><dt>{{ label }}</dt><dd>{{ selected[key] }}</dd></template><dt>حالة المناقصة</dt><dd>{{ statusText(selected.status) }}</dd><template v-for="[key, label] in [['announceStart', 'بداية الإعلان'], ['announceEnd', 'نهاية الإعلان'], ['reminderDate', 'تاريخ التذكير']]" :key="key"><dt>{{ label }}</dt><dd>{{ formatContractDate(selected[key]) }}</dd></template></dl>
        <h3>فض العروض (محاضر)</h3><div v-if="selected.bids.length" class="table-scroll"><table><thead><tr><th>رقم المحضر</th><th>التاريخ</th><th>الموضوع</th></tr></thead><tbody><tr v-for="(row, index) in selected.bids" :key="index"><td>{{ row.number }}</td><td>{{ formatContractDate(row.date) }}</td><td class="request-summary">{{ row.subject }}</td></tr></tbody></table></div><p v-else class="empty-state">لا توجد محاضر محفوظة.</p>
        <h3>الرغبات</h3><ol v-if="selected.wishes.length" class="request-wishes"><li v-for="(wish, index) in selected.wishes" :key="index">{{ wish }}</li></ol><p v-else class="empty-state">لا توجد رغبات محفوظة.</p>
      </template>
    </BaseModal>
    <BaseModal :model-value="!!removal" title="حذف العقد" :busy="busy" @update:model-value="removal = null"><p v-if="error" class="error" role="alert">{{ error }}</p><p>هل تريد حذف العقد رقم {{ removal?.id }} من القائمة؟</p><template #footer><button type="button" class="btn--danger" :disabled="busy" @click="remove">تأكيد الحذف</button><button type="button" class="btn--secondary" :disabled="busy" @click="removal = null">إلغاء</button></template></BaseModal>
  </main>
</template>
<style scoped>
.request-filters { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 1rem; margin-block-end: 1rem; }
.requests-table { min-width: 1100px; }
.request-summary { min-width: 13rem; max-width: 24rem; white-space: pre-wrap; overflow-wrap: anywhere; }
.request-pagination { display: flex; flex-wrap: wrap; gap: 1rem; justify-content: flex-end; align-items: center; margin-block-start: 1rem; }
.request-detail { display: grid; grid-template-columns: minmax(7rem, 1fr) 3fr; margin: 0; }
.request-detail dt, .request-detail dd { padding: .8rem; margin: 0; border-bottom: 1px solid var(--color-border); overflow-wrap: anywhere; white-space: pre-wrap; }
.request-detail dt { background: var(--color-muted-surface); font-weight: 700; }
.request-wishes li { padding: .8rem; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 640px) { .request-filters, .request-detail { grid-template-columns: 1fr; } }
</style>
