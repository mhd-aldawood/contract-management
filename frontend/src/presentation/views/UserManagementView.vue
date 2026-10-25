<template>
  <div class="page" dir="rtl">
    <main class="content">
      <PageHeader
        icon="👥"
        eyebrow="إدارة النظام"
        title="إدارة المستخدمين"
        description="إنشاء الحسابات وتعيين الأدوار والتحكم بحالة الوصول من مكان واحد."
      >
        <template #actions>
          <button type="button" @click="openCreateModal">＋ إضافة مستخدم</button>
        </template>
      </PageHeader>

      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <section v-if="temporaryCredential" class="credential">
        <strong>بيانات الدخول المؤقتة — تظهر مرة واحدة فقط</strong>
        <span>المستخدم: <code>{{ temporaryCredential.username }}</code></span>
        <span>كلمة المرور: <code dir="ltr">{{ temporaryCredential.password }}</code></span>
        <button type="button" @click="copyCredential">نسخ البيانات</button>
      </section>

      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>قائمة المستخدمين</h2>
            <p>{{ users.length }} مستخدم ضمن النتائج الحالية</p>
          </div>
        </div>
        <form class="filters" @submit.prevent="loadUsers">
          <input v-model.trim="filters.q" placeholder="بحث بالاسم أو البريد" />
          <select v-model="filters.role">
            <option value="">كل الأدوار</option>
            <option v-for="role in roles" :key="role.code" :value="role.code">{{ role.name }}</option>
          </select>
          <select v-model="filters.active">
            <option value="">كل الحالات</option>
            <option value="true">فعال</option>
            <option value="false">غير فعال</option>
          </select>
          <button type="submit">تصفية</button>
        </form>

        <p v-if="loading">جارٍ تحميل المستخدمين...</p>
        <div v-else class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>اسم المستخدم</th>
                <th>البريد الإلكتروني</th>
                <th>الدور</th>
                <th>الحالة</th>
                <th>كلمة المرور</th>
                <th>الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.email || '—' }}</td>
                <td>{{ roleName(user.roleCode) }}</td>
                <td>
                  <StatusBadge :tone="user.isActive ? 'success' : 'danger'">
                    {{ user.isActive ? 'فعال' : 'غير فعال' }}
                  </StatusBadge>
                  <small v-if="user.mustChangePassword">يجب تغيير كلمة المرور</small>
                </td>
                <td>
                  <button type="button" class="btn--secondary btn--sm" :disabled="user.id === currentUserId" @click="resetPassword(user)">إعادة تعيين</button>
                </td>
                <td class="table-actions">
                  <button type="button" class="btn--secondary btn--sm" :disabled="saving === user.id" @click="openEditModal(user)">تعديل</button>
                  <button
                    type="button"
                    class="btn--sm"
                    :class="user.isActive ? 'btn--danger' : 'btn--success'"
                    :disabled="user.isSuperuser || user.id === currentUserId || saving === user.id"
                    @click="toggleActive(user)"
                  >
                    {{ user.isActive ? 'إلغاء التفعيل' : 'تفعيل' }}
                  </button>
                </td>
              </tr>
              <tr v-if="users.length === 0"><td colspan="6">لا توجد نتائج.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <BaseModal
      v-model="modalOpen"
      :title="modalMode === 'create' ? 'إضافة مستخدم جديد' : 'تعديل بيانات المستخدم'"
      :description="modalMode === 'create' ? 'أدخل بيانات الحساب وحدد دوره في النظام.' : 'حدّث البيانات ثم احفظ التغييرات.'"
      eyebrow="إدارة المستخدمين"
      :busy="saving === 'modal'"
      @close="closeModal"
    >
      <form id="user-form" class="modal-form-grid" @submit.prevent="submitUser">
        <label class="form-field">
          <span>اسم المستخدم</span>
          <input
            v-model.trim="userForm.username"
            :disabled="modalMode === 'edit' && userForm.id === currentUserId"
            autocomplete="off"
            required
          />
        </label>
        <label class="form-field">
          <span>البريد الإلكتروني</span>
          <input v-model.trim="userForm.email" type="email" />
        </label>
        <label class="form-field modal-form-grid__wide">
          <span>الدور</span>
          <select v-model="userForm.roleCode" :disabled="userForm.isSuperuser" required>
            <option value="" disabled>اختر الدور</option>
            <option v-for="role in roles" :key="role.code" :value="role.code">{{ role.name }}</option>
          </select>
        </label>

        <details v-if="selectedUserRole" class="permission-preview modal-form-grid__wide">
          <summary class="permission-preview__heading">
            <div>
              <strong>صلاحيات دور {{ selectedUserRole.name }}</strong>
              <small>عرض الميزات والصلاحيات التي يرثها المستخدم من هذا الدور.</small>
            </div>
          </summary>
          <div class="permission-preview__list">
            <div v-for="feature in features" :key="feature.code" class="permission-preview__row">
              <span>{{ feature.nameAr }}</span>
              <span class="permission-preview__badges">
                <StatusBadge v-if="selectedUserRole.permissions[feature.code]?.read" tone="info">قراءة</StatusBadge>
                <StatusBadge v-if="selectedUserRole.permissions[feature.code]?.write" tone="success">كتابة</StatusBadge>
                <StatusBadge
                  v-if="!selectedUserRole.permissions[feature.code]?.read && !selectedUserRole.permissions[feature.code]?.write"
                  tone="neutral"
                >
                  بدون وصول
                </StatusBadge>
              </span>
            </div>
          </div>
        </details>

        <p v-if="modalMode === 'create'" class="modal-note modal-form-grid__wide">
          سيتم توليد كلمة مرور مؤقتة وإظهارها مرة واحدة بعد إنشاء الحساب.
        </p>

      </form>
      <template #footer>
        <button type="submit" form="user-form" :disabled="saving === 'modal'">
          {{ saving === 'modal' ? 'جارٍ الحفظ...' : (modalMode === 'create' ? 'إنشاء المستخدم' : 'حفظ التعديلات') }}
        </button>
        <button type="button" class="btn--secondary" @click="closeModal">إلغاء</button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import container from '@/di/container'
import BaseModal from '@/presentation/components/BaseModal.vue'
import PageHeader from '@/presentation/components/PageHeader.vue'
import StatusBadge from '@/presentation/components/StatusBadge.vue'

const users = ref([])
const roles = ref([])
const features = ref([])
const loading = ref(true)
const saving = ref(null)
const error = ref('')
const temporaryCredential = ref(null)
const currentUserId = computed(() => container.authRepository.getCurrentUser()?.id)
const filters = reactive({ q: '', role: '', active: '' })
const modalOpen = ref(false)
const modalMode = ref('create')
const userForm = reactive({ id: null, username: '', email: '', roleCode: '', isSuperuser: false })
const selectedUserRole = computed(() => roles.value.find((role) => role.code === userForm.roleCode) || null)

function mapUser(user) {
  return { ...user, roleCode: user.role?.code || '' }
}

function roleName(roleCode) {
  return roles.value.find((role) => role.code === roleCode)?.name || 'بدون دور'
}

function openCreateModal() {
  modalMode.value = 'create'
  Object.assign(userForm, { id: null, username: '', email: '', roleCode: '', isSuperuser: false })
  modalOpen.value = true
}

function openEditModal(user) {
  modalMode.value = 'edit'
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    email: user.email || '',
    roleCode: user.roleCode,
    isSuperuser: user.isSuperuser,
  })
  modalOpen.value = true
}

function closeModal() {
  if (saving.value === 'modal') return
  modalOpen.value = false
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    users.value = (await container.authRepository.getUsers({ ...filters })).map(mapUser)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function load() {
  error.value = ''
  try {
    const matrix = await container.authRepository.getAccessControl()
    roles.value = matrix.roles
    features.value = matrix.features
    await loadUsers()
  } catch (e) {
    error.value = e.message
    loading.value = false
  }
}

async function createUser() {
  saving.value = 'modal'
  error.value = ''
  try {
    const result = await container.authRepository.createUser({
      username: userForm.username,
      email: userForm.email,
      roleCode: userForm.roleCode,
    })
    temporaryCredential.value = {
      username: result.user.username,
      password: result.temporaryPassword,
    }
    modalOpen.value = false
    await loadUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = null
  }
}

async function saveUser() {
  saving.value = 'modal'
  error.value = ''
  try {
    const result = await container.authRepository.updateUser(userForm.id, {
      username: userForm.username,
      email: userForm.email,
      roleCode: userForm.roleCode,
    })
    const index = users.value.findIndex((user) => user.id === userForm.id)
    if (index >= 0) users.value[index] = mapUser(result.user)
    modalOpen.value = false
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = null
  }
}

function submitUser() {
  return modalMode.value === 'create' ? createUser() : saveUser()
}

async function toggleActive(user) {
  saving.value = user.id
  error.value = ''
  try {
    const result = await container.authRepository.updateUser(user.id, {
      isActive: !user.isActive,
    })
    Object.assign(user, mapUser(result.user))
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = null
  }
}

async function resetPassword(user) {
  if (!window.confirm(`توليد كلمة مرور مؤقتة جديدة للمستخدم ${user.username}؟`)) return
  saving.value = user.id
  error.value = ''
  try {
    const result = await container.authRepository.updateUser(user.id, { resetPassword: true })
    Object.assign(user, mapUser(result.user))
    temporaryCredential.value = {
      username: result.user.username,
      password: result.temporaryPassword,
    }
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = null
  }
}

async function copyCredential() {
  const value = `Username: ${temporaryCredential.value.username}\nPassword: ${temporaryCredential.value.password}`
  await navigator.clipboard.writeText(value)
}

onMounted(load)
</script>

<style scoped>
.credential { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; margin-block-end: 1.25rem; }
.credential strong { width: 100%; color: var(--color-success); }
.credential code { user-select: all; }
.panel-heading p { margin: 0.25rem 0 0; color: var(--color-text-muted); font-size: 0.85rem; }
.filters { margin-block-start: 1rem; }
.table-scroll { margin-block-start: 1rem; }
table { width: 100%; min-width: 1100px; border-collapse: collapse; }
td small { display: block; margin-block-start: 0.35rem; color: var(--color-warning); }
.modal-form { display: grid; gap: 1rem; }
.modal-note { margin: 0; padding: 0.75rem; color: var(--color-warning); background: var(--color-warning-bg); border-radius: var(--radius-sm); }
.permission-preview { overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.permission-preview__heading { padding: 1rem; background: var(--color-primary-50); cursor: pointer; }
.permission-preview[open] .permission-preview__heading { border-bottom: 1px solid var(--color-border); }
.permission-preview__heading > div { display: inline-grid; vertical-align: middle; gap: 0.2rem; }
.permission-preview__heading:focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: -2px; }
.permission-preview__heading small { color: var(--color-text-muted); }
.permission-preview__list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.permission-preview__row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.65rem 0.8rem; border-bottom: 1px solid var(--color-border); }
.permission-preview__row:last-child { border-bottom: 0; }
.permission-preview__badges { display: flex; flex-wrap: wrap; gap: 0.35rem; }
@container modal-body (max-width: 40rem) {
  .permission-preview__list { grid-template-columns: 1fr; }
}
</style>
