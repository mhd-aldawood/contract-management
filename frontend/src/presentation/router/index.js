import { createRouter, createWebHistory } from 'vue-router'
import container from '@/di/container'
import { ROUTE_PATHS, ROUTE_NAMES } from '@/core/config'

const routes = [
  { path: '/', redirect: '/signup' },
  {
    path: ROUTE_PATHS.signup,
    name: ROUTE_NAMES.signup,
    component: () => import('@/presentation/views/SignupView.vue')
  },
  {
    path:ROUTE_PATHS.login ,
    name: ROUTE_NAMES.login,
    component: () => import('@/presentation/views/LoginView.vue')
  },
  {
    path:ROUTE_PATHS.home,
    name: ROUTE_NAMES.home,
    component: () => import('@/presentation/views/HomeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path:ROUTE_PATHS.profile,
    name:ROUTE_NAMES.profile,
    component: () => import('@/presentation/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path:ROUTE_PATHS.settings ,
    name:ROUTE_NAMES.settings,
    component: () => import('@/presentation/views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path:ROUTE_PATHS.about,
    name:ROUTE_NAMES.about,
    component: () => import('@/presentation/views/AboutView.vue'),
    meta: { requiresAuth: true }
  },
  {
     path:ROUTE_PATHS.planning, 
     name:ROUTE_NAMES.planning,
     component: () => import('@/presentation/views/AgreementsView.vue'),  
    },
    {
  path:ROUTE_PATHS.contracts.nafathCenters,
  name:ROUTE_NAMES.contracts.nafathCenters,
  component: () => import('@/presentation/views/contracts/NafathCentersView.vue'),
  meta: { requiresAuth: true },
},
{
  path:ROUTE_PATHS.contracts.memorandum,
  name:ROUTE_NAMES.contracts.memorandum,
  component: () => import('@/presentation/views/contracts/MemorandumView.vue'),
  meta: { requiresAuth: true },
},
{
  path:ROUTE_PATHS.contracts.lifelongLearning,
  name: ROUTE_NAMES.contracts.lifelongLearning,
  component: () => import('@/presentation/views/contracts/LifelongLearningView.vue'),
  meta: { requiresAuth: true },
},
{
  path:ROUTE_PATHS.contracts.otherAgreements,// '/home/contracts/other',
  name:ROUTE_NAMES.contracts.otherAgreements, //'other-agreements',
  component: () => import('@/presentation/views/contracts/OtherAgreementsView.vue'),
  meta: { requiresAuth: true },
},
{
  path:ROUTE_PATHS.contracts.educationalContent,// '/home/contracts/educational-content',
  name:ROUTE_NAMES.contracts.educationalContent,// 'educational-contentView',
  component: () => import('@/presentation/views/contracts/EducationalContentView.vue'),
  meta: { requiresAuth: true },
},
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const user = container.authRepository.getCurrentUser()
  if (to.meta.requiresAuth && !user) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router