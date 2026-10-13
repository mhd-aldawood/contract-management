import { Agreement } from '@/domain/entities/Agreement';

const RAW_AGREEMENTS = [
  {
    number: 1001,
    name: 'اتفاقية صيانة المبنى',
    startDate: '2026-01-10',
    endDate: '2026-06-30',
    workDetails: 'أعمال الصيانة العامة للمبنى',
    status: 'finish',
    cost: 25000,
    costDetails: 'صيانة سنوية',
    type: 'current',
    showCostTable: false,
  },
  {
    number: 1002,
    name: 'اتفاقية تطوير البرمجيات',
    startDate: '2026-03-01',
    endDate: '2026-12-31',
    workDetails: 'تطوير تطبيق الهاتف المحمول',
    status: 'current',
    cost: 75000,
    costDetails: 'التطوير والدعم الفني',
    type: 'investment',
    showCostTable: false,
  },
  {
    number: 1003,
    name: 'اتفاقية الخدمات الأمنية',
    startDate: '2027-01-01',
    endDate: '2027-12-31',
    workDetails: 'خدمات الأمن والمراقبة',
    status: 'future',
    cost: null,
    costDetails: 'خدمات أمنية',
    type: 'current',
    showCostTable: true,
  },
  {
    number: 1004,
    name: 'اتفاقية البنية التحتية للشبكة',
    startDate: '2025-01-01',
    endDate: '2025-12-31',
    workDetails: 'صيانة البنية التحتية للشبكة',
    status: 'finish',
    cost: 40000,
    costDetails: 'صيانة البنية التحتية',
    type: 'investment',
    showCostTable: false,
  },
  {
    number: 1005,
    name: 'اتفاقية خدمات التنظيف',
    startDate: '2026-02-01',
    endDate: '2026-08-31',
    workDetails: 'خدمات تنظيف المكاتب',
    status: 'current',
    cost: null,
    costDetails: 'خدمات تنظيف شهرية',
    type: 'current',
    showCostTable: true,
  },
  {
    number: 1006,
    name: 'اتفاقية الصيانة الكهربائية',
    startDate: '2025-05-01',
    endDate: '2026-05-01',
    workDetails: 'أعمال الصيانة والإصلاحات الكهربائية',
    status: 'finish',
    cost: 32000,
    costDetails: 'خدمات كهربائية',
    type: 'investment',
    showCostTable: false,
  },
];

const RAW_COST_DETAILS = [
  { years: 'أول 5 سنوات', percentage: '40%', details: 'قسط الطلاب - الفترة الأولى' },
  { years: 'ثاني 3 سنوات', percentage: '30%', details: 'قسط الطلاب - الفترة الثانية' },
  { years: 'ثالث 2 سنوات', percentage: '30%', details: 'قسط الطلاب - الفترة الثالثة' },
];

export class AgreementLocalDataSource {
  async fetchAll() {
    return RAW_AGREEMENTS.map((r) => new Agreement(r));
  }
  async fetchCostDetails() {
    return RAW_COST_DETAILS;
  }
}