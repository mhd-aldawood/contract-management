/* ---------- nested validation for payment rows ---------- */
import {
  required, maxLength, numeric, min, 
} from './rules'
export const paymentRowSchema = {
  amount: [
    required('المبلغ مطلوب'),
    numeric('المبلغ يجب أن يكون رقمًا'),
    min(0.01, 'المبلغ يجب أن يكون أكبر من صفر'),
  ],
  dueDate: [required('تاريخ الدفعة مطلوب')],
  label: [maxLength(250)],
}