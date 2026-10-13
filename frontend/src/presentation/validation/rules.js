// src/presentation/validation/rules.js

const isEmpty = (v) =>
  v === null || v === undefined || (typeof v === 'string' && v.trim() === '')

export const required = (msg = 'هذا الحقل مطلوب') => (value) =>
  isEmpty(value) ? msg : ''

export const minLength = (n, msg) => (value) =>
  isEmpty(value) || String(value).trim().length >= n
    ? ''
    : msg || `يجب ألا يقل عن ${n} أحرف`

export const maxLength = (n, msg) => (value) =>
  isEmpty(value) || String(value).trim().length <= n
    ? ''
    : msg || `يجب ألا يزيد عن ${n} حرفًا`

export const numeric = (msg = 'يجب إدخال قيمة رقمية صحيحة') => (value) =>
  isEmpty(value) || Number.isFinite(Number(value)) ? '' : msg

export const min = (limit, msg) => (value) =>
  isEmpty(value) || Number(value) >= limit
    ? ''
    : msg || `القيمة يجب ألا تقل عن ${limit}`

export const max = (limit, msg) => (value) =>
  isEmpty(value) || Number(value) <= limit
    ? ''
    : msg || `القيمة يجب ألا تزيد عن ${limit}`

export const oneOf = (list, msg = 'قيمة غير صالحة') => (value) =>
  isEmpty(value) || list.includes(value) ? '' : msg

export const pattern = (regex, msg) => (value) =>
  isEmpty(value) || regex.test(String(value)) ? '' : msg

/** Cross-field / arbitrary checks. `predicate(value, form)` must return true when valid. */
export const custom = (predicate, msg) => (value, form) =>
  predicate(value, form) ? '' : msg