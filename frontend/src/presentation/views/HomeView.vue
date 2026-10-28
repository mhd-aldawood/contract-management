<script setup>
import { getAccessToken } from '@/core/api/authSession'

import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { API_URLS } from '@/core/config/apiUrls'
import { apiRequest } from '@/core/api/apiClient'
import container from '@/di/container'
import { NAV_GROUPS } from '@/presentation/config/navigation'
import { contractPhase, formatContractDate } from '@/presentation/utils/contractDates'
import PageHeader from '@/presentation/components/PageHeader.vue'
import DashboardDonut from '@/presentation/components/DashboardDonut.vue'

const user = computed(() => container.authRepository.getCurrentUser())
const dashboard = ref(null)
const loading = ref(true)
const error = ref('')
let requestVersion = 0
const roleNames = { admin: 'مسؤول النظام', dean: 'العميد', finance: 'المالية', contract: 'العقود', planning: 'التخطيط' }
const purposes = {
  admin: 'نظرة عامة على الاتفاقيات، المستخدمين وأوامر الصرف.',
  dean: 'متابعة الاتفاقيات وأوامر الصرف والتحكم بظهورها في التخطيط.',
  finance: 'متابعة أوامر الصرف والاتفاقيات التي تحتاج إلى ملفات مالية.',
  contract: 'متابعة الاتفاقيات الجديدة، تواريخ التذكير ومواعيد الانتهاء.',
  planning: 'متابعة الاتفاقيات الظاهرة للتخطيط حسب تواريخها ومواعيد انتهائها.',
}
const mode = computed(() => dashboard.value?.mode || user.value?.role?.code || 'custom')
const roleName = computed(() => roleNames[mode.value] || user.value?.role?.name || 'المستخدم')
const description = computed(() => 'أهلاً بك، ' + (user.value?.username || '') + '. ' + (purposes[mode.value] || 'مؤشرات الميزات المتاحة لك حسب صلاحياتك.'))
const canRead = feature => container.authRepository.hasPermission(feature, 'read')
const isAdmin = computed(() => container.authRepository.isAdmin())
const number = value => new Intl.NumberFormat('ar-SY').format(value || 0)
const colors = ['var(--color-primary-600)', 'var(--color-info)', 'var(--color-text-muted)']
const phaseLabels = { current: 'حالية', future: 'مستقبلية', finish: 'منتهية' }
const phases = computed(() => (dashboard.value?.charts.phases || []).map((item, index) => ({ ...item, color: colors[index] })))
const coverage = computed(() => dashboard.value?.finance ? [
  { code: 'with', label: 'لديها أوامر صرف', count: dashboard.value.finance.withOrders, color: 'var(--color-primary-600)' },
  { code: 'without', label: 'تحتاج إلى أوامر صرف', count: dashboard.value.finance.withoutOrders, color: 'var(--color-warning)' },
] : [])
const stats = computed(() => {
  if (!dashboard.value) return []
  const d = dashboard.value, a = d.agreements
  const common = [
    { label: 'العقود والاتفاقيات', value: a.total, hint: mode.value === 'planning' ? 'الظاهرة للتخطيط فقط' : 'ضمن الميزات المتاحة لك' },
    { label: 'اتفاقيات جديدة هذا الشهر', value: a.newThisMonth, hint: 'حسب تاريخ الإضافة' },
    { label: 'تذكيرات مستحقة', value: a.remindersDue, hint: 'للاتفاقيات غير المنتهية' },
    { label: 'تنتهي خلال ٣٠ يوماً', value: a.expiringSoon, hint: 'تشمل الاتفاقيات المنتهية اليوم' },
  ]
  if (mode.value === 'finance' && d.finance) return [
    { label: 'أوامر الصرف', value: d.finance.orderCount, hint: 'الملفات المالية الحالية' },
    { label: 'اتفاقيات دون أمر صرف', value: d.finance.withoutOrders, hint: 'تحتاج إلى متابعة مالية' },
    { label: 'أوامر مضافة هذا الشهر', value: d.finance.ordersThisMonth, hint: 'حسب تاريخ رفع الملف' }, common[0],
  ]
  if (mode.value === 'dean') return [common[0], ...(d.users ? [{ label: 'المستخدمون', value: d.users.total, hint: number(d.users.active) + ' حساب فعال' }] : []),
    { label: 'مخفية عن التخطيط', value: a.hidden, hint: 'متاحة للمراجعة لدى العميد' }, common[3]]
  if (mode.value === 'planning') return [common[0], { label: 'اتفاقيات حالية', value: a.current, hint: 'سارية حسب تاريخ البداية والنهاية' },
    { label: 'اتفاقيات مستقبلية', value: a.future, hint: 'لم تبدأ بعد' }, common[3]]
  if (mode.value === 'admin') return [common[0], ...(d.users ? [
    { label: 'المستخدمون الفعالون', value: d.users.active, hint: number(d.users.total) + ' حساب إجمالاً' },
    { label: 'الأدوار', value: d.users.roles, hint: 'أدوار النظام والأدوار المخصصة' },
  ] : []), ...(d.finance ? [{ label: 'أوامر الصرف', value: d.finance.orderCount, hint: number(d.finance.withoutOrders) + ' اتفاقية دون أوامر' }] : [])]
  return common
})
const links = computed(() => {
  const priority = { admin: ['users', 'roles', 'dean', 'finance', 'planning', 'settings'], dean: ['dean', 'finance', 'planning'],
    finance: ['finance', 'planning'], contract: ['nafath-centers', 'memorandum', 'lifelong-learning', 'other-agreements', 'educational-content', 'doctoral-contracts', 'planning'], planning: ['planning'] }[mode.value] || []
  return NAV_GROUPS.filter(group => !group.adminOnly || isAdmin.value).flatMap(group => group.items)
    .filter(item => item.name !== 'home' && !['profile', 'about'].includes(item.name) && (!item.adminOnly || isAdmin.value) &&
      (!item.hideForAdmin || !isAdmin.value) && (!item.feature || canRead(item.feature)))
    .sort((a, b) => (priority.includes(a.name) ? priority.indexOf(a.name) : 99) - (priority.includes(b.name) ? priority.indexOf(b.name) : 99)).slice(0, 8)
})
const financeMode = computed(() => mode.value === 'finance' && !!dashboard.value?.finance)
const typeMaximum = computed(() => Math.max(1, ...(dashboard.value?.charts.types || []).map(item => financeMode.value ? item.orderCount : item.count)))
const monthMaximum = computed(() => Math.max(1, ...(dashboard.value?.charts.monthly || []).flatMap(item => [item.agreements, item.orders || 0])))
function monthLabel(value) {
  const [year, month] = value.split('-').map(Number)
  return new Intl.DateTimeFormat('ar-SY-u-ca-gregory', { month: 'short' }).format(new Date(year, month - 1, 1))
}
function typeLink(feature) {
  if (mode.value === 'planning' && canRead('planning')) return { path: '/planning', query: { type: feature } }
  if (mode.value === 'finance' && canRead('finance')) return { path: '/finance', query: { type: feature } }
  if (canRead('dean')) return { path: '/dean', query: { type: feature } }
  if (canRead(feature)) return { path: '/contracts/' + feature }
  return { path: '/planning', query: { type: feature } }
}
function documentLink(record) {
  if (mode.value === 'finance' && canRead('finance')) return { path: '/finance', query: { document: record.key || record.agreementKey } }
  if (canRead('dean')) return { path: '/dean', query: { document: record.key || record.agreementKey } }
  const target = typeLink(record.feature)
  return { ...target, query: { ...target.query, q: record.agreementNumber } }
}
async function load() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  try {
    const response = await apiRequest(API_URLS.dashboard, { headers: { Authorization: 'Token ' + getAccessToken() } })
    if (version === requestVersion) dashboard.value = response.data
  } catch (e) { if (version === requestVersion) error.value = e.message }
  finally { if (version === requestVersion) loading.value = false }
}
onMounted(load)
onBeforeUnmount(() => { requestVersion++ })
</script>

<template>
  <main class="app-page dashboard" dir="rtl" :aria-busy="loading">
    <PageHeader title="لوحة التحكم" :eyebrow="roleName" :description="description">
      <template #actions><button type="button" class="btn--secondary" :disabled="loading" @click="load">{{ loading ? 'جارٍ التحديث…' : 'تحديث البيانات' }}</button></template>
    </PageHeader>
    <div v-if="error" class="error" role="alert">{{ error }} <button type="button" class="btn--secondary btn--sm" @click="load">إعادة المحاولة</button></div>
    <p v-if="loading && !dashboard" class="panel empty-state" role="status">جارٍ تحميل مؤشرات لوحة التحكم…</p>
    <template v-if="dashboard">
      <p class="dashboard-date">بيانات حقيقية من النظام · {{ formatContractDate(dashboard.today) }} · {{ dashboard.scope === 'planning-visible' ? 'الاتفاقيات الظاهرة للتخطيط' : 'حسب الميزات والصلاحيات المتاحة لك' }}</p>
      <section class="dashboard-stats" aria-label="المؤشرات الرئيسية">
        <article v-for="stat in stats" :key="stat.label" class="panel dashboard-stat"><h2>{{ stat.label }}</h2><strong>{{ number(stat.value) }}</strong><p>{{ stat.hint }}</p></article>
      </section>
    </template>
    <section class="panel dashboard-shortcuts" aria-labelledby="dashboard-shortcuts-title">
      <div class="panel-heading"><h2 id="dashboard-shortcuts-title">وصول سريع</h2><span class="dashboard-caption">الأقسام المتاحة لحسابك</span></div>
      <nav class="dashboard-links" aria-label="وصول سريع"><RouterLink v-for="link in links" :key="link.path" :to="link.path"><span>{{ link.label }}</span><span aria-hidden="true">←</span></RouterLink></nav>
      <p v-if="!links.length" class="dashboard-caption">لا توجد أقسام إضافية متاحة لهذا الحساب.</p>
    </section>
    <template v-if="dashboard">
      <div class="dashboard-charts">
        <section class="panel dashboard-chart" aria-labelledby="dashboard-status-title">
          <h2 id="dashboard-status-title">حالة الاتفاقيات</h2><p class="dashboard-caption">حسب تاريخي البداية والنهاية، بتوقيت دمشق.</p>
          <DashboardDonut :items="phases" label="اتفاقيات مصنّفة" />
          <p v-if="!phases.some(item => item.count)" class="dashboard-caption">لا توجد اتفاقيات ذات فترة زمنية قابلة للتصنيف.</p>
        </section>
        <section class="panel dashboard-chart" aria-labelledby="dashboard-types-title">
          <h2 id="dashboard-types-title">{{ financeMode ? 'أوامر الصرف حسب نوع الاتفاقية' : 'الاتفاقيات حسب النوع' }}</h2><p class="dashboard-caption">اضغط على النوع لفتح القائمة المرتبطة به.</p>
          <div class="dashboard-type-bars">
            <RouterLink v-for="item in dashboard.charts.types" :key="item.feature" :to="typeLink(item.feature)" class="dashboard-type-bar">
              <span>{{ item.label }}</span><strong>{{ number(financeMode ? item.orderCount : item.count) }}</strong>
              <span class="dashboard-bar-track" aria-hidden="true"><span :style="{ width: ((financeMode ? item.orderCount : item.count) / typeMaximum * 100) + '%' }"></span></span>
            </RouterLink>
            <p v-if="!dashboard.charts.types.length" class="dashboard-caption">لا توجد ميزات اتفاقيات متاحة لحسابك.</p>
          </div>
        </section>
        <section class="panel dashboard-chart" :class="{ 'dashboard-chart--wide': !dashboard.finance }" aria-labelledby="dashboard-monthly-title">
          <h2 id="dashboard-monthly-title">النشاط خلال آخر ٦ أشهر</h2><p class="dashboard-caption">عدد الاتفاقيات المضافة{{ dashboard.finance ? ' وأوامر الصرف المرفوعة' : '' }}، حسب شهر الإضافة.</p>
          <div class="dashboard-chart-legend"><span><i class="agreements-color"></i>اتفاقيات</span><span v-if="dashboard.finance"><i class="orders-color"></i>أوامر صرف</span></div>
          <div class="dashboard-months">
            <div v-for="month in dashboard.charts.monthly" :key="month.month" class="dashboard-month" :aria-label="month.month + ': ' + month.agreements + ' اتفاقية' + (dashboard.finance ? '، ' + month.orders + ' أمر صرف' : '')">
              <div class="dashboard-month__bars" aria-hidden="true"><div><span>{{ number(month.agreements) }}</span><i class="agreements-color" :style="{ height: (month.agreements / monthMaximum * 100) + '%' }"></i></div><div v-if="dashboard.finance"><span>{{ number(month.orders) }}</span><i class="orders-color" :style="{ height: (month.orders / monthMaximum * 100) + '%' }"></i></div></div>
              <strong>{{ monthLabel(month.month) }}</strong>
            </div>
          </div>
        </section>
        <section v-if="dashboard.finance" class="panel dashboard-chart" aria-labelledby="dashboard-finance-title">
          <h2 id="dashboard-finance-title">تغطية الاتفاقيات بأوامر الصرف</h2><p class="dashboard-caption">الأوامر المحذوفة لا تُحتسب. هذه أعداد ملفات، وليست مبالغ مدفوعة.</p>
          <DashboardDonut :items="coverage" label="عقود واتفاقيات" />
        </section>
      </div>
      <section v-if="financeMode" class="panel" aria-labelledby="dashboard-orders-title">
        <div class="panel-heading"><h2 id="dashboard-orders-title">آخر أوامر الصرف المرفوعة</h2><RouterLink to="/finance">الانتقال إلى المالية ←</RouterLink></div>
        <ul class="dashboard-recent-orders"><li v-for="order in dashboard.recentOrders" :key="order.id"><RouterLink :to="documentLink(order)"><span><strong>{{ order.title }}</strong><small>{{ order.agreementName }}</small></span><time>{{ formatContractDate(order.createdAt) }}</time><span aria-hidden="true">←</span></RouterLink></li></ul>
        <p v-if="!dashboard.recentOrders.length" class="empty-state">لم تُرفع أوامر صرف بعد.</p>
      </section>
      <section class="panel" aria-labelledby="dashboard-recent-title">
        <div class="panel-heading"><h2 id="dashboard-recent-title">آخر الاتفاقيات المحدّثة</h2><span class="dashboard-caption">آخر ٥ اتفاقيات ضمن نطاق وصولك</span></div>
        <div class="table-scroll"><table><thead><tr><th>العقد / الاتفاقية</th><th>الرقم والنوع</th><th>الحالة</th><th>تاريخ التذكير</th><th>الإجراء</th></tr></thead><tbody>
          <tr v-for="record in dashboard.recentAgreements" :key="record.key"><td class="dashboard-agreement-name">{{ record.name || '—' }}</td><td>{{ record.agreementNumber }}<small class="dashboard-cell-note">{{ record.category }}</small></td><td><span class="status-badge" :class="'status-' + contractPhase(record, dashboard.today)">{{ phaseLabels[contractPhase(record, dashboard.today)] || '—' }}</span></td><td>{{ formatContractDate(record.reminderDate) }}</td><td><RouterLink :to="documentLink(record)">فتح الاتفاقية ←</RouterLink></td></tr>
          <tr v-if="!dashboard.recentAgreements.length"><td colspan="5" class="empty-state">لا توجد اتفاقيات متاحة بعد. ستظهر المؤشرات تلقائياً عند إضافة البيانات.</td></tr>
        </tbody></table></div>
      </section>
    </template>
  </main>
</template>

<style scoped>
.dashboard-date, .dashboard-caption { color: var(--color-text-muted); font-size: 0.85rem; line-height: 1.7; }
.dashboard-date { margin-block-end: 1rem; }
.dashboard-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem; margin-block-end: 1.25rem; }
.dashboard-stat { margin: 0; padding: 1.35rem; border-block-start: 3px solid var(--color-primary-600); }
.dashboard-stat h2 { margin: 0 0 0.75rem; font-size: 0.9rem; color: var(--color-text-muted); }
.dashboard-stat > strong { font-size: clamp(1.8rem, 3vw, 2.5rem); font-variant-numeric: tabular-nums; }
.dashboard-stat p { margin: 0.5rem 0 0; font-size: 0.8rem; line-height: 1.6; color: var(--color-text-muted); }
.dashboard-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr)); gap: 0.65rem; }
.dashboard-links a { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.85rem 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-sm); text-decoration: none; color: var(--color-text); font-size: 0.9rem; font-weight: 700; }
.dashboard-links a:hover, .dashboard-links a:focus-visible { background: var(--color-primary-50); border-color: var(--color-primary-600); }
.dashboard-charts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.25rem; margin-block-end: 1.25rem; }
.dashboard-chart { min-width: 0; margin: 0; padding: 1.5rem; }
.dashboard-chart > h2 { font-size: 1.1rem; margin: 0; }
.dashboard-chart > .dashboard-caption { margin-block: 0.5rem 1.4rem; }
.dashboard-chart--wide { grid-column: 1 / -1; }
.dashboard-type-bars { display: grid; gap: 1rem; }
.dashboard-type-bar { display: grid; grid-template-columns: 1fr auto; gap: 0.45rem; color: var(--color-text); text-decoration: none; font-size: 0.85rem; }
.dashboard-type-bar:focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 4px; }
.dashboard-bar-track { display: block; grid-column: 1 / -1; height: 0.55rem; overflow: hidden; border-radius: 999px; background: var(--color-muted-surface); }
.dashboard-bar-track > span { display: block; height: 100%; border-radius: inherit; background: var(--color-primary-600); }
.dashboard-chart-legend { display: flex; flex-wrap: wrap; gap: 1rem; margin-block-end: 1.5rem; font-size: 0.8rem; }
.dashboard-chart-legend > span { display: flex; gap: 0.4rem; align-items: center; }
.dashboard-chart-legend i { width: 0.65rem; height: 0.65rem; border-radius: 2px; }
.agreements-color { background: var(--color-primary-600); }.orders-color { background: var(--color-info); }
.dashboard-months { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 0.5rem; direction: ltr; }
.dashboard-month { min-width: 0; text-align: center; }.dashboard-month > strong { font-size: 0.72rem; font-weight: 500; }
.dashboard-month__bars { height: 10rem; display: flex; align-items: end; justify-content: center; gap: 0.3rem; margin-block-end: 0.5rem; border-bottom: 1px solid var(--color-border); }
.dashboard-month__bars > div { height: 8rem; flex: 0 1 1.4rem; position: relative; display: flex; align-items: end; }
.dashboard-month__bars i { display: block; width: 100%; min-height: 2px; border-radius: 3px 3px 0 0; }
.dashboard-month__bars span { position: absolute; inset: -1.5rem 0 auto; font-size: 0.7rem; }
.dashboard-cell-note { display: block; margin-block-start: 0.3rem; color: var(--color-text-muted); }
.dashboard-agreement-name { min-width: 12rem; max-width: 24rem; white-space: normal; overflow-wrap: anywhere; }
.dashboard-recent-orders { list-style: none; padding: 0; margin: 0; }.dashboard-recent-orders li + li { border-top: 1px solid var(--color-border); }
.dashboard-recent-orders a { display: flex; align-items: center; gap: 1rem; padding-block: 1rem; text-decoration: none; color: var(--color-text); }
.dashboard-recent-orders a > span:first-child { flex: 1; min-width: 0; overflow-wrap: anywhere; }.dashboard-recent-orders small { display: block; margin-block-start: 0.4rem; color: var(--color-text-muted); }
.dashboard-recent-orders time { flex-shrink: 0; color: var(--color-text-muted); font-size: 0.8rem; }
@media (max-width: 1100px) { .dashboard-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } .dashboard-charts { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .dashboard-stat, .dashboard-chart { padding: 1rem; } .dashboard-stats { gap: 0.6rem; } .dashboard-stat h2 { font-size: 0.8rem; } .dashboard-recent-orders a { flex-wrap: wrap; } .dashboard .panel-heading { flex-wrap: wrap; } }
</style>
