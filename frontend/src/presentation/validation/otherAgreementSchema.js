import {
  required, minLength, maxLength, numeric, min, custom,pattern
} from './rules'

export const otherAgreementSchema = {
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
  
 startDate: [required('تاريخ بداية الاتفاقية مطلوب')],

  endDate: [
    required('تاريخ نهاية الاتفاقية مطلوب'),
    custom(
      (v, form) =>
        !v || !form.startDate || new Date(v).getTime() > new Date(form.startDate).getTime(),
      'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
    ),
  ],

};