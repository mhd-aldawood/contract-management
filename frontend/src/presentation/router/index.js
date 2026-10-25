import { createRouter, createWebHistory } from 'vue-router'
import container from '@/di/container'
import { ROUTE_PATHS, ROUTE_NAMES } from '@/core/config'

const routes = [
  {
    path: ROUTE_PATHS.finance,
    name: ROUTE_NAMES.finance,
    component: () => import('@/presentation/views/FinanceView.vue'),
    meta: { requiresAuth: true, feature: 'finance', action: 'read' },
  },
  { path: '/', redirect: '/login' },
  {
    path:ROUTE_PATHS.login ,
    name: ROUTE_NAMES.login,
    component: () => import('@/presentation/views/LoginView.vue')
  },
  {
    path:ROUTE_PATHS.home,
    name: ROUTE_NAMES.home,
    component: () => import('@/presentation/views/HomeView.vue'),
    meta: { requiresAuth: true, feature: 'home', action: 'read' }
  },
  {
    path:ROUTE_PATHS.profile,
    name:ROUTE_NAMES.profile,
    component: () => import('@/presentation/views/ProfileView.vue'),
    meta: { requiresAuth: true, feature: 'profile', action: 'read' }
  },
  {
    path:ROUTE_PATHS.settings ,
    name:ROUTE_NAMES.settings,
    component: () => import('@/presentation/views/SettingsView.vue'),
    meta: { requiresAuth: true, feature: 'settings', action: 'read' }
  },
  {
    path:ROUTE_PATHS.about,
    name:ROUTE_NAMES.about,
    component: () => import('@/presentation/views/AboutView.vue'),
    meta: { requiresAuth: true, feature: 'about', action: 'read' }
  },
  {
     path:ROUTE_PATHS.planning, 
     name:ROUTE_NAMES.planning,
     component: () => import('@/presentation/views/contracts/ContractListView.vue'),
     props: { feature: 'planning' },
     meta: { requiresAuth: true, feature: 'planning', action: 'read' },
    },
    {
  path:ROUTE_PATHS.contracts.nafathCenters,
  name:ROUTE_NAMES.contracts.nafathCenters,
  component: () => import('@/presentation/views/contracts/ContractListView.vue'),
  props: { feature: 'nafath-centers' },
  meta: { requiresAuth: true, feature: 'nafath-centers', action: 'read' },
},
{
  path:ROUTE_PATHS.contracts.memorandum,
  name:ROUTE_NAMES.contracts.memorandum,
  component: () => import('@/presentation/views/contracts/ContractListView.vue'),
  props: { feature: 'memorandum' },
  meta: { requiresAuth: true, feature: 'memorandum', action: 'read' },
},
{
  path:ROUTE_PATHS.contracts.lifelongLearning,
  name: ROUTE_NAMES.contracts.lifelongLearning,
  component: () => import('@/presentation/views/contracts/ContractListView.vue'),
  props: { feature: 'lifelong-learning' },
  meta: { requiresAuth: true, feature: 'lifelong-learning', action: 'read' },
},
{
  path:ROUTE_PATHS.contracts.otherAgreements,// '/home/contracts/other',
  name:ROUTE_NAMES.contracts.otherAgreements, //'other-agreements',
  component: () => import('@/presentation/views/contracts/ContractListView.vue'),
  props: { feature: 'other-agreements' },
  meta: { requiresAuth: true, feature: 'other-agreements', action: 'read' },
},
{
  path:ROUTE_PATHS.contracts.educationalContent,// '/home/contracts/educational-content',
  name:ROUTE_NAMES.contracts.educationalContent,// 'educational-contentView',
  component: () => import('@/presentation/views/contracts/ContractListView.vue'),
  props: { feature: 'educational-content' },
  meta: { requiresAuth: true, feature: 'educational-content', action: 'read' },
},
{
  path: ROUTE_PATHS.roles,
  name: ROUTE_NAMES.roles,
  component: () => import('@/presentation/views/AccessControlView.vue'),
  meta: { requiresAuth: true, feature: 'access-control', action: 'read', adminOnly: true },
},
{
  path: ROUTE_PATHS.accessControl,
  name: ROUTE_NAMES.accessControl,
  redirect: ROUTE_PATHS.roles,
  meta: { requiresAuth: true, feature: 'access-control', action: 'read', adminOnly: true },
},
{
  path: ROUTE_PATHS.forbidden,
  name: ROUTE_NAMES.forbidden,
  component: () => import('@/presentation/views/ForbiddenView.vue'),
  meta: { requiresAuth: true },
},
{
  path: ROUTE_PATHS.users,
  name: ROUTE_NAMES.users,
  component: () => import('@/presentation/views/UserManagementView.vue'),
  meta: { requiresAuth: true, feature: 'user-management', action: 'read', adminOnly: true },
},
{
  path: ROUTE_PATHS.changePassword,
  name: ROUTE_NAMES.changePassword,
  component: () => import('@/presentation/views/ChangePasswordView.vue'),
  meta: { requiresAuth: true, allowPasswordChange: true },
},
// Catch-all: prevents a blank white screen when a URL matches no route.
{
  path: '/:pathMatch(.*)*',
  name: 'not-found',
  component: () => import('@/presentation/views/NotFoundView.vue'),
},
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  let user = container.authRepository.getCurrentUser()
  if (to.meta.requiresAuth && user) {
    try {
      user = await container.authRepository.ensureCurrentUser()
    } catch {
      await container.authRepository.logout()
      return next({ name: ROUTE_NAMES.login })
    }
  }
  if (to.meta.requiresAuth && !user) {
    next({ name: 'login' })
  } else if (user?.mustChangePassword && !to.meta.allowPasswordChange) {
    next({ name: ROUTE_NAMES.changePassword })
  } else if (to.meta.adminOnly && !container.authRepository.isAdmin()) {
    next({ name: ROUTE_NAMES.forbidden })
  } else if (
    to.meta.feature &&
    !container.authRepository.hasPermission(to.meta.feature, to.meta.action || 'read')
  ) {
    next({ name: ROUTE_NAMES.forbidden })
  } else {
    next()
  }
})

export default router
