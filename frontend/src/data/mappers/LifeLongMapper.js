
// Exactly the keys the backend expects (camelCase = wire names).
const LIFE_LONG_KEYS = [
    'type',
    'agreementNumber',
    'name',
    'companyName',
    'subject',
    'startDate',
    'endDate',
    'reminderDate',
    'paymentMethod',
    'paymentText',
    'paymentSchedule',
    'status',
    'disbursement',
    'budgetType',
    'fileName',
    'file',
    'isHidden'
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
  const payload = pick(form, LIFE_LONG_KEYS)

  if (Array.isArray(form.paymentSchedule)) {
    payload.paymentSchedule = form.paymentSchedule.map((row) => pick(row, ROW_KEYS))
  }

  return payload
}
