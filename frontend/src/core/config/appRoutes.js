// src/core/config/appRoutes.js

export const ROUTE_NAMES = {
  home: 'home',
  about: 'about',
  login: 'login',
  signup: 'signup',
  profile: 'profile',
  settings: 'settings',
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
  signup: '/signup',
  profile: '/profile',
  settings: '/settings',
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