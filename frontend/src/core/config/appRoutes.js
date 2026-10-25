// src/core/config/appRoutes.js

export const ROUTE_NAMES = {
  home: 'home',
  about: 'about',
  login: 'login',
  profile: 'profile',
  settings: 'settings',
  accessControl: 'access-control',
  roles: 'roles',
  forbidden: 'forbidden',
  users: 'users',
  changePassword: 'change-password',
  agreements: 'agreements',
  planning:'planning',
  contracts: {
    educationalContent: 'educational-content',
    lifelongLearning: 'lifelong-learning',
    memorandum: 'memorandum',
    nafathCenters: 'nafath-centers',
    otherAgreements: 'other-agreements',
  },
}

export const ROUTE_PATHS = {
  home: '/home',
  about: '/about',
  login: '/login',
  profile: '/profile',
  settings: '/settings',
  accessControl: '/admin/access-control',
  roles: '/admin/roles',
  forbidden: '/forbidden',
  users: '/admin/users',
  changePassword: '/change-password',
  agreements: '/agreements',
  planning: '/planning',
  contracts: {
    educationalContent: '/contracts/educational-content',
    lifelongLearning:   '/contracts/lifelong-learning',
    memorandum:         '/contracts/memorandum',
    nafathCenters:      '/contracts/nafath-centers',
    otherAgreements:    '/contracts/other-agreements',
  },
}
