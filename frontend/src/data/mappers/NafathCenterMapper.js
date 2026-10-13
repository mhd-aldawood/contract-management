// data/mappers/NafathCenterMapper.js

// Exactly the keys the backend expects (camelCase = wire names).
const AGREEMENT_KEYS = [
  'type',
  'agreementNumber',
  'name',
  'companyName',
  'subject',
  'estimatedCost',
  'startDate',
  'endDate',
  'paymentMethod',
  'paymentText',
  'status',
  'disbursement',
  'budgetType',
  'isHidden',
  'fileName', 
  'file'
]

const ROW_KEYS = ['label', 'amount', 'dueDate']

function pick(obj, keys) {
  const out = {}
  for (const k of keys) {
    if (obj[k] !== undefined) out[k] = obj[k]
  }
  return out
}

/**
 * Domain form → API payload.
 * Strips UI-only keys (errors, touched, dirty, computed getters, ...).
 */
export function toApiPayload(form) {
  const payload = pick(form, AGREEMENT_KEYS)

  if (Array.isArray(form.paymentSchedule)) {
    payload.paymentSchedule = form.paymentSchedule.map((row) => pick(row, ROW_KEYS))
  }

  return payload
}