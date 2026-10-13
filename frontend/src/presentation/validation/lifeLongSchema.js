// src/presentation/validation/educationalContentSchema.js
import {
  required, minLength, maxLength, numeric, min, oneOf, custom,pattern
} from './rules'

export const lifeLongSchema = {
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
  paymentText: [
    custom(
      (v, f) => f.paymentMethod !== 'text' || (v && String(v).trim().length > 0),
      'يرجى إدخال تفاصيل الدفع'
    ),
    maxLength(2000),
  ],

  paymentSchedule: [
    custom(
      (rows, f) =>
        f.paymentMethod !== 'table' || (Array.isArray(rows) && rows.length > 0),
      'يجب إضافة صف دفع واحد على الأقل'
    ),
  ],
}

/* ---------- nested validation for payment rows ---------- */
export const paymentRowSchema = {
  amount: [
    required('المبلغ مطلوب'),
    numeric('المبلغ يجب أن يكون رقمًا'),
    min(0.01, 'المبلغ يجب أن يكون أكبر من صفر'),
  ],
  dueDate: [required('تاريخ الدفعة مطلوب')],
  label: [maxLength(250)],
}

export function validatePaymentRows(rows = []) {
  return rows.map((row) => {
    const rowErrors = {}
    for (const [field, rules] of Object.entries(paymentRowSchema)) {
      for (const rule of rules) {
        const msg = rule(row[field], row)
        if (msg) { rowErrors[field] = msg; break }
      }
    }
    return rowErrors
  })
}