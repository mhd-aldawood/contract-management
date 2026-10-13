// src/presentation/validation/nafathCentersSchema.js
import {
  required, minLength, maxLength, numeric, min, oneOf, custom,pattern
} from './rules'

export const nafathCentersSchema = {
  agreementNumber: [
    required('رقم الاتفاقية مطلوب'),
    pattern(/^[A-Za-z0-9\-\/]+$/, 'رقم الاتفاقية يقبل الأحرف والأرقام و - / فقط'),
    maxLength(50),
  ],
  name: [
    required('اسم الاتفاقية مطلوب'),
    minLength(3, 'اسم الاتفاقية قصير جدًا'),
    maxLength(150),
  ],
  companyName: [
    required('اسم الشركة المتعاقد معها مطلوب'),
    minLength(3, 'اسم الشركة قصير جدًا'),
    maxLength(150),
  ],
  
 subject: [
    required('موضوع الاتفاقية مطلوب'),
    minLength(5, 'موضوع الاتفاقية قصير جدًا'),
    maxLength(500),
  ],

  estimatedCost: [
    required('الكلفة التقديرية مطلوبة'),
    numeric('الكلفة التقديرية يجب أن تكون رقمًا'),
    min(0, 'الكلفة التقديرية لا يمكن أن تكون سالبة'),
  ],
  
 startDate: [required('تاريخ بداية الاتفاقية مطلوب')],

  endDate: [
    required('تاريخ نهاية الاتفاقية مطلوب'),
    custom(
      (v, form) =>
        !v || !form.startDate || new Date(v).getTime() > new Date(form.startDate).getTime(),
      'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
    ),
  ],

  
  // ✅ ADD these in its place:
  paymentMethod: [
    required('يجب اختيار طريقة الدفع'),
    oneOf(['text', 'table'], 'طريقة الدفع غير صالحة'),
  ],

  status: [
    required('حالة الاتفاقية مطلوبة'),
    maxLength(50),
  ],

  disbursement: [maxLength(250)],
  
  budgetType: [
    required('نوع الموازنة مطلوب'),
    oneOf(['current', 'investment'], 'نوع الموازنة غير صالح'),
  ],



};