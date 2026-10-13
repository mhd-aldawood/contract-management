// src/presentation/config/navigation.js
export const NAV_ITEMS = [
  {
    name: 'profile',
    label: 'الحساب',
    icon: '👤',
    path: '/profile',
  },
  {
    name: 'settings',
    label: 'الاعدادات',
    icon: '⚙️',
    path: '/settings',
  },
  {
    name: 'about',
    label: 'حول',
    icon: 'ℹ️',
    path: '/about',
  },
  {
    name: 'planning',
    label: 'التخطيط',
    icon: '📋',
    path: '/planning',
  },
  {
    name: 'contracts',
    label: 'العقود',
    icon: '📑',
    children: [
      {
        name: 'nafath-centers',
        label: 'مراكز النفاذ',
        icon: '🏢',
        path: '/contracts/nafath-centers',
      },
      {
        name: 'memorandum',
        label: 'اتفاقية مذكرة تفاهم',
        icon: '📝',
        path: '/contracts/memorandum',
      },
      {
        name: 'lifelong-learning',
        label: 'اتفاقية مركز التعلم مدى الحياة',
        icon: '🎓',
        path: '/contracts/lifelong-learning',
      },
      {
        name: 'other-agreements',
        label: 'اتفاقيات أخرى',
        icon: '📄',
        path: '/contracts/other',
      },
       {
        name: 'educational-content',
        label: 'محتوى تعليمي',
        icon: '📄',
        path: '/contracts/educational-content',
      },
    ],
  },
]