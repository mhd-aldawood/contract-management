// src/presentation/validation/educationalContentSchema.js
import {
  required, minLength, maxLength, numeric, min, oneOf, custom,pattern
} from './rules'

export const educationalContentSchema = {
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

  additionalCourses: [maxLength(500)],

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

  quarterlyDue: [
    required('المبلغ المستحق الفصلي مطلوب'),
    numeric('المبلغ المستحق الفصلي يجب أن يكون رقمًا'),
    min(0, 'المبلغ المستحق الفصلي لا يمكن أن يكون سالبًا'),
    custom(
      (v, form) =>
        v === '' || v == null || !form.estimatedCost ||
        Number(v) <= Number(form.estimatedCost),
      'المبلغ المستحق الفصلي لا يمكن أن يتجاوز الكلفة التقديرية'
    ),
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

  contractText: [maxLength(20000, 'نص العقد طويل جدًا')],

    paymentMethod: [
    required('يجب اختيار طريقة الدفع'),
    oneOf(['text', 'table'], 'طريقة الدفع غير صالحة'),
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
/**
 * Validate the paymentSchedule array.
 * @param {Array<{label:string, amount:number, dueDate:string}>} rows
 * @returns {Array<Object>} array of per-row error objects ({} when a row is valid)
 */
export function validatePaymentSchedule(rows = []) {
  if (!Array.isArray(rows)) return []

  return rows.map((row) => {
    const rowErrors = {}
    for (const [field, rules] of Object.entries(paymentRowSchema)) {
      for (const rule of rules) {
        const msg = rule(row[field], row)
        if (msg) {
          rowErrors[field] = msg
          break // stop at first error per field
        }
      }
    }
    return rowErrors
  })
}