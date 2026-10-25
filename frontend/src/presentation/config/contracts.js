import { API_URLS } from '@/core/config/apiUrls'

export const CONTRACT_TYPES = [
  { feature: 'nafath-centers', title: 'اتفاقيات مراكز النفاذ', endpoint: API_URLS.nafathCenter.list },
  { feature: 'memorandum', title: 'مذكرات التفاهم', endpoint: API_URLS.memorandum.list },
  { feature: 'lifelong-learning', title: 'اتفاقيات التعلم مدى الحياة', endpoint: API_URLS.lifeLong.list },
  { feature: 'other-agreements', title: 'اتفاقيات أخرى', endpoint: API_URLS.otherAgreement.list },
  { feature: 'educational-content', title: 'اتفاقيات المحتوى التعليمي', endpoint: API_URLS.educationalContents.list },
]
