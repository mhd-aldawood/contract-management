export const NAV_GROUPS = [
  {
    key: 'main',
    label: 'الرئيسية',
    items: [
      { name: 'home', label: 'لوحة التحكم', icon: '⌂', path: '/home', feature: 'home' },
      { name: 'planning', label: 'التخطيط والاتفاقيات', icon: '▤', path: '/planning', feature: 'planning' },
      { name: 'finance', label: 'المالية وأوامر الصرف', icon: '▥', path: '/finance', feature: 'finance' },
      { name: 'dean', label: 'العميد ومراجعة الاتفاقيات', icon: '▧', path: '/dean', feature: 'dean' },
    ],
  },
  {
    key: 'contracts',
    label: 'العقود',
    items: [
      { name: 'contract-requests', label: 'إضافة عقد', icon: '＋', path: '/contracts/create', feature: 'contract-requests' },
      { name: 'nafath-centers', label: 'مراكز النفاذ', icon: '▣', path: '/contracts/nafath-centers', feature: 'nafath-centers' },
      { name: 'memorandum', label: 'مذكرات التفاهم', icon: '▧', path: '/contracts/memorandum', feature: 'memorandum' },
      { name: 'lifelong-learning', label: 'التعلم مدى الحياة', icon: '◈', path: '/contracts/lifelong-learning', feature: 'lifelong-learning' },
      { name: 'other-agreements', label: 'اتفاقيات أخرى', icon: '◇', path: '/contracts/other-agreements', feature: 'other-agreements' },
      { name: 'educational-content', label: 'المحتوى التعليمي', icon: '▦', path: '/contracts/educational-content', feature: 'educational-content' },
      { name: 'doctoral-contracts', label: 'عقد الدكتوراه', icon: '▤', path: '/contracts/doctoral-contracts', feature: 'doctoral-contracts' },
    ],
  },
  {
    key: 'administration',
    label: 'إدارة النظام',
    adminOnly: true,
    items: [
      { name: 'settings', label: 'الإعدادات', icon: '⚙', path: '/settings', adminOnly: true },
      { name: 'security', label: 'الأمان والجلسات', icon: '◆', path: '/admin/security', feature: 'security-settings', adminOnly: true },
      { name: 'users', label: 'المستخدمون', icon: '♙', path: '/admin/users', feature: 'user-management', adminOnly: true },
      { name: 'roles', label: 'الأدوار والصلاحيات', icon: '◆', path: '/admin/roles', feature: 'access-control', adminOnly: true },
    ],
  },
  {
    key: 'account',
    label: 'الحساب',
    items: [
      { name: 'profile', label: 'الحساب الشخصي', icon: '○', path: '/profile', feature: 'profile' },
      { name: 'settings', label: 'الإعدادات', icon: '⚙', path: '/settings', feature: 'settings', hideForAdmin: true },
      { name: 'about', label: 'حول النظام', icon: 'ⓘ', path: '/about', feature: 'about' },
    ],
  },
]

export const NAV_ITEMS = NAV_GROUPS.flatMap((group) => group.items)
