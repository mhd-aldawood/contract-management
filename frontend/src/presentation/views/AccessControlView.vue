<template>
  <div class="page" dir="rtl">
    <main class="content">
      <PageHeader
        icon="🔐"
        eyebrow="الأمان والصلاحيات"
        title="إدارة الأدوار والصلاحيات"
        description="القراءة تتيح عرض البيانات، والكتابة تتيح الإضافة والتعديل والحذف وتغيير حالة السجلات."
      />

      <p v-if="loading" class="status">جارٍ تحميل الصلاحيات...</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <template v-if="matrix && !loading">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>اختيار الدور</h2>
              <p>اختر دوراً واحداً لإدارته. لن تمتد الصفحة أفقياً عند إضافة أدوار جديدة.</p>
            </div>
            <button type="button" @click="openCreateRoleModal">＋ إضافة دور</button>
          </div>

          <div class="role-selector">
            <label class="form-field role-select-field">
              <span>الدور المراد إدارته</span>
              <select v-model="selectedRoleCode">
                <option v-for="role in matrix.roles" :key="role.code" :value="role.code">
                  {{ role.name }}
                </option>
              </select>
            </label>

            <div v-if="selectedRole" class="selected-role-summary">
              <span>
                <strong>{{ selectedRole.name }}</strong>
                <code>{{ selectedRole.code }}</code>
              </span>
              <StatusBadge :tone="systemRoles.has(selectedRole.code) ? 'info' : 'neutral'">
                {{ systemRoles.has(selectedRole.code) ? 'دور أساسي' : 'دور مخصص' }}
              </StatusBadge>
              <span class="table-actions">
                <button
                  type="button"
                  class="btn--secondary btn--sm"
                  :disabled="selectedRole.code === 'admin' || savingKey === `role:${selectedRole.code}`"
                  @click="openEditRoleModal(selectedRole)"
                >
                  تعديل الاسم
                </button>
                <button
                  v-if="!systemRoles.has(selectedRole.code)"
                  type="button"
                  class="btn--danger btn--sm"
                  :disabled="savingKey === `role:${selectedRole.code}`"
                  @click="deleteRole(selectedRole)"
                >
                  حذف الدور
                </button>
              </span>
            </div>
          </div>
        </section>

        <section v-if="selectedRole" class="panel">
          <div class="panel-heading">
            <div>
              <h2>صلاحيات دور {{ selectedRole.name }}</h2>
              <p>كل ميزة مستقلة. الكتابة تفعّل القراءة تلقائياً، وإلغاء القراءة يلغي الكتابة.</p>
            </div>
          </div>
          <div class="feature-list">
            <article v-for="feature in matrix.features" :key="feature.code" class="feature-row">
              <div class="feature-identity">
                <strong>{{ feature.nameAr }}</strong>
                <code>{{ feature.code }}</code>
              </div>
              <div class="permission-options">
                <label>
                  <input
                    type="checkbox"
                    :checked="selectedRole.permissions[feature.code]?.read"
                    :disabled="selectedRole.code === 'admin' || savingKey === `${selectedRole.code}:${feature.code}`"
                    @change="changePermission(selectedRole, feature.code, 'read', $event.target.checked)"
                  />
                  <span><strong>قراءة</strong><small>عرض الصفحة والبيانات</small></span>
                </label>
                <label>
                  <input
                    type="checkbox"
                    :checked="selectedRole.permissions[feature.code]?.write"
                    :disabled="selectedRole.code === 'admin' || savingKey === `${selectedRole.code}:${feature.code}`"
                    @change="changePermission(selectedRole, feature.code, 'write', $event.target.checked)"
                  />
                  <span><strong>كتابة</strong><small>إضافة وتعديل وحذف</small></span>
                </label>
              </div>
            </article>
          </div>
        </section>
      </template>
    </main>

    <BaseModal
      v-model="roleModalOpen"
      :title="roleModalMode === 'create' ? 'إضافة دور جديد' : 'تعديل الدور'"
      description="استخدم اسماً عربياً واضحاً يعبّر عن مسؤولية أصحاب هذا الدور."
      eyebrow="إدارة الأدوار"
      :busy="savingKey === 'role-modal'"
      @close="closeRoleModal"
    >
      <form id="role-form" class="modal-form-grid" @submit.prevent="submitRole">
        <label class="form-field">
          <span>رمز الدور</span>
          <input
            v-model.trim="roleForm.code"
            type="text"
            dir="ltr"
            pattern="[a-z0-9_-]+"
            placeholder="auditor"
            :disabled="roleModalMode === 'edit'"
            required
          />
          <small class="field-hint">أحرف إنكليزية صغيرة وأرقام وشرطة فقط، ولا يمكن تغييره لاحقاً.</small>
        </label>
        <label class="form-field">
          <span>اسم الدور</span>
          <input v-model.trim="roleForm.name" type="text" placeholder="مثال: مدقق العقود" required />
        </label>
      </form>
      <template #footer>
        <button type="submit" form="role-form" :disabled="savingKey === 'role-modal'">
          {{ savingKey === 'role-modal' ? 'جارٍ الحفظ...' : (roleModalMode === 'create' ? 'إضافة الدور' : 'حفظ التعديلات') }}
        </button>
        <button type="button" class="btn--secondary" @click="closeRoleModal">إلغاء</button>
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

const matrix = ref(null)
const loading = ref(true)
const error = ref('')
const savingKey = ref('')
const roleModalOpen = ref(false)
const roleModalMode = ref('create')
const roleForm = reactive({ code: '', name: '' })
const selectedRoleCode = ref('')
const systemRoles = new Set(['admin', 'dean', 'contract', 'planning', 'finance'])
const selectedRole = computed(() => matrix.value?.roles.find((role) => role.code === selectedRoleCode.value) || null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    matrix.value = await container.authRepository.getAccessControl()
    if (!matrix.value.roles.some((role) => role.code === selectedRoleCode.value)) {
      selectedRoleCode.value = matrix.value.roles[0]?.code || ''
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function changePermission(role, feature, action, checked) {
  const current = role.permissions[feature] || { read: false, write: false }
  const next = { ...current, [action]: checked }
  if (action === 'write' && checked) next.read = true
  if (action === 'read' && !checked) next.write = false

  savingKey.value = `${role.code}:${feature}`
  error.value = ''
  try {
    matrix.value = await container.authRepository.updateAccessControl({
      roleCode: role.code,
      feature,
      read: next.read,
      write: next.write,
    })
  } catch (e) {
    error.value = e.message
  } finally {
    savingKey.value = ''
  }
}

function openCreateRoleModal() {
  roleModalMode.value = 'create'
  Object.assign(roleForm, { code: '', name: '' })
  roleModalOpen.value = true
}

function openEditRoleModal(role) {
  roleModalMode.value = 'edit'
  Object.assign(roleForm, { code: role.code, name: role.name })
  roleModalOpen.value = true
}

function closeRoleModal() {
  if (savingKey.value === 'role-modal') return
  roleModalOpen.value = false
}

async function submitRole() {
  savingKey.value = 'role-modal'
  error.value = ''
  try {
    if (roleModalMode.value === 'create') {
      const createdCode = roleForm.code.toLowerCase()
      matrix.value = await container.authRepository.createRole({
        roleCode: createdCode,
        roleName: roleForm.name,
      })
      selectedRoleCode.value = createdCode
    } else {
      matrix.value = await container.authRepository.updateAccessControl({
        roleCode: roleForm.code,
        roleName: roleForm.name.trim(),
      })
    }
    roleModalOpen.value = false
  } catch (e) {
    error.value = e.message
  } finally {
    savingKey.value = ''
  }
}

async function deleteRole(role) {
  if (!window.confirm(`حذف الدور ${role.name}؟ سيتم إلغاء ربطه بالحسابات.`)) return
  savingKey.value = `role:${role.code}`
  error.value = ''
  try {
    matrix.value = await container.authRepository.deleteRole(role.code)
    selectedRoleCode.value = matrix.value.roles[0]?.code || ''
  } catch (e) {
    error.value = e.message
  } finally {
    savingKey.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.panel-heading p { margin: 0.25rem 0 0; color: var(--color-text-muted); font-size: 0.85rem; }
.role-selector { display: grid; grid-template-columns: minmax(16rem, 1fr) minmax(20rem, 2fr); gap: 1rem; align-items: end; }
.selected-role-summary { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.8rem; min-height: 4.7rem; padding: 0.85rem 1rem; background: var(--color-muted-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.selected-role-summary > span:first-child { display: grid; gap: 0.2rem; }
.selected-role-summary code, .feature-identity code { width: max-content; direction: ltr; color: var(--color-text-muted); font-size: 0.76rem; }
.feature-list { display: grid; gap: 0.65rem; }
.feature-row { display: grid; grid-template-columns: minmax(14rem, 1fr) minmax(20rem, 1.4fr); gap: 1rem; align-items: center; padding: 0.9rem 1rem; border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.feature-identity { display: grid; gap: 0.2rem; }
.permission-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }
.permission-options label { display: flex; align-items: center; gap: 0.65rem; padding: 0.65rem; background: var(--color-muted-surface); border: 1px solid var(--color-border); border-radius: var(--radius-sm); }
.permission-options label > span { display: grid; gap: 0.15rem; }
.permission-options small { color: var(--color-text-muted); font-size: 0.75rem; }
input[type='checkbox'] { width: 1rem; height: 1rem; }
select { min-width: 130px; }
.modal-form { display: grid; gap: 1rem; }
@media (max-width: 800px) {
  .role-selector, .feature-row { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .permission-options { grid-template-columns: 1fr; }
}
</style>
