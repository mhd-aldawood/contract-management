<script setup>
import { computed, reactive, ref } from 'vue'
import { apiRequest } from '@/core/api/apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import { damascusToday } from '@/presentation/utils/contractDates'
import ModalFormActions from '@/presentation/components/ModalFormActions.vue'
import { useFeatureAccess } from '@/presentation/composables/useFeatureAccess'
const props = defineProps({ initialValue: { type: Object, default: null } })
const emit = defineEmits(['saved', 'busy'])
const { canWrite } = useFeatureAccess('contract-requests')
const emptyBid = () => ({ number: '', date: '', subject: '' })
const defaults = () => ({ justificationMemo: '', technicalSpecs: '', legalSpecs: '', announceStart: damascusToday(), announceEnd: '', reminderDate: '', status: '', bids: [emptyBid()], wishes: [] })
const form = reactive(defaults())
const error = ref(''), saving = ref(false)
function reset() {
  Object.assign(form, defaults(), props.initialValue ? { ...props.initialValue,
    bids: props.initialValue.bids.length ? props.initialValue.bids.map(row => ({ ...row })) : [emptyBid()],
    wishes: [...props.initialValue.wishes],
  } : {})
  error.value = ''
}
reset()
const actualBids = computed(() => form.bids.filter(row => row.number.trim() || row.date || row.subject.trim()))
const valid = computed(() => form.justificationMemo.trim() && form.technicalSpecs.trim() && form.legalSpecs.trim() && form.reminderDate &&
  ['success', 'failed'].includes(form.status) && (form.status === 'failed' || (form.announceStart && form.announceEnd && form.announceEnd >= form.announceStart &&
    actualBids.value.every(row => row.number.trim() && row.date && row.subject.trim()))))
async function save() {
  if (!canWrite.value || !valid.value || saving.value) return
  saving.value = true; emit('busy', true); error.value = ''
  try {
    const payload = { justificationMemo: form.justificationMemo.trim(), technicalSpecs: form.technicalSpecs.trim(), legalSpecs: form.legalSpecs.trim(),
      reminderDate: form.reminderDate, status: form.status,
      announceStart: form.status === 'success' ? form.announceStart : null, announceEnd: form.status === 'success' ? form.announceEnd : null,
      bids: form.status === 'success' ? actualBids.value.map(row => ({ ...row, number: row.number.trim(), subject: row.subject.trim() })) : [],
      wishes: form.status === 'success' ? form.wishes.map(row => row.trim()).filter(Boolean) : [],
    }
    const response = await apiRequest(props.initialValue ? API_URLS.contractRequests.byId(props.initialValue.id) : API_URLS.contractRequests.list,
      { method: props.initialValue ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
    emit('saved', response)
  } catch (e) { error.value = e.message }
  finally { saving.value = false; emit('busy', false) }
}
</script>
<template>
  <form dir="rtl" @submit.prevent="save">
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <fieldset class="permission-fieldset" :disabled="saving || !canWrite">
      <section class="agreement-form-section"><h3>البيانات الأساسية</h3><div class="agreement-form-grid">
        <label class="form-field request-wide"><span>مذكرة تبريرية *</span><textarea v-model="form.justificationMemo" maxlength="20000" rows="3" placeholder="أدخل المذكرة التبريرية" required></textarea></label>
        <label class="form-field"><span>دفتر شروط فني *</span><input v-model="form.technicalSpecs" maxlength="2000" placeholder="أدخل دفتر الشروط الفني" required /></label>
        <label class="form-field"><span>دفتر شروط حقوقي *</span><input v-model="form.legalSpecs" maxlength="2000" placeholder="أدخل دفتر الشروط الحقوقي" required /></label>
        <label class="form-field"><span>تاريخ التذكير *</span><input v-model="form.reminderDate" type="date" required /></label>
      </div></section>
      <section class="agreement-form-section"><h3>حالة المناقصة</h3><div class="request-status">
        <label><input v-model="form.status" type="radio" value="success" name="tender-status" /> تمت المناقصة بنجاح</label>
        <label><input v-model="form.status" type="radio" value="failed" name="tender-status" /> فشلت المناقصة</label>
      </div>
        <p v-if="form.status === 'failed'" class="notice" role="status">عند حفظ حالة الفشل، لن تُحفظ تواريخ الإعلان أو محاضر فض العروض أو الرغبات. تبقى المذكرة ودفاتر الشروط وتاريخ التذكير محفوظة.</p>
      </section>
      <template v-if="form.status !== 'failed'">
        <section class="agreement-form-section"><h3>تواريخ الإعلان</h3><div class="agreement-form-grid">
          <label class="form-field"><span>تاريخ الإعلان (بداية) *</span><input v-model="form.announceStart" type="date" required /></label>
          <label class="form-field"><span>تاريخ الإعلان (نهاية) *</span><input v-model="form.announceEnd" type="date" :min="form.announceStart" required /></label>
        </div><p v-if="form.announceStart && form.announceEnd && form.announceEnd < form.announceStart" class="field-error">تاريخ النهاية يجب ألا يسبق تاريخ البداية.</p></section>
        <section class="agreement-form-section"><div class="panel-heading"><h3>فض العروض (محاضر)</h3><button type="button" class="btn--secondary btn--sm" :disabled="form.bids.length >= 100" @click="form.bids.push(emptyBid())">إضافة محضر</button></div>
          <p class="field-hint">يمكن ترك الصف فارغاً. عند إدخال محضر، أكمل رقمه وتاريخه وموضوعه.</p>
          <fieldset v-for="(row, index) in form.bids" :key="index" class="request-row"><legend>محضر {{ index + 1 }}</legend><div class="request-bid-fields">
            <label class="form-field"><span>رقم المحضر</span><input v-model="row.number" maxlength="150" /></label>
            <label class="form-field"><span>التاريخ</span><input v-model="row.date" type="date" /></label>
            <label class="form-field"><span>الموضوع</span><input v-model="row.subject" maxlength="2000" /></label>
            <button type="button" class="btn--danger btn--sm" :aria-label="`حذف المحضر ${index + 1}`" @click="form.bids.splice(index, 1)">حذف</button>
          </div></fieldset>
        </section>
        <section class="agreement-form-section"><div class="panel-heading"><h3>الرغبات</h3><button type="button" class="btn--secondary btn--sm" :disabled="form.wishes.length >= 100" @click="form.wishes.push('')">إضافة رغبة جديدة</button></div>
          <div v-for="(_, index) in form.wishes" :key="index" class="request-wish"><label class="form-field"><span>الرغبة {{ index + 1 }}</span><textarea v-model="form.wishes[index]" maxlength="2000" rows="2" placeholder="أدخل الرغبة"></textarea></label><button type="button" class="btn--danger btn--sm" :aria-label="`حذف الرغبة ${index + 1}`" @click="form.wishes.splice(index, 1)">حذف</button></div>
        </section>
      </template>
    </fieldset>
    <ModalFormActions><button type="submit" :disabled="!valid || saving || !canWrite" @click.prevent="save">{{ saving ? 'جارٍ الحفظ…' : 'حفظ العقد' }}</button><button type="button" class="btn--secondary" :disabled="saving" @click="reset">إعادة تعيين</button></ModalFormActions>
  </form>
</template>
<style scoped>
.request-wide { grid-column: 1 / -1; }
.request-status { display: flex; flex-wrap: wrap; gap: 1rem; }
.request-status label { display: flex; gap: .6rem; align-items: center; padding: .8rem 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-muted-surface); }
.request-status input { width: 1.1rem; height: 1.1rem; }
.request-row { min-width: 0; margin-block: 1rem; padding: 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-muted-surface); }
.request-bid-fields { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.5fr) auto; gap: .8rem; align-items: end; }
.request-bid-fields > * { min-width: 0; }
.request-wish { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .8rem; align-items: end; margin-block: .8rem; }
@container modal-body (max-width: 40rem) { .request-bid-fields, .request-wish { grid-template-columns: 1fr; }.request-bid-fields button, .request-wish button { justify-self: start; } }
</style>
