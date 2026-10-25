// Date-only values stay calendar dates; UTC parsing must not shift their day.
export function formatContractDate(value) {
  if (!value) return '—'
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return '—'
  return new Intl.DateTimeFormat('ar-SY-u-ca-gregory', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date(year, month - 1, day))
}

export function damascusToday(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Damascus', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now)
  const value = type => parts.find(part => part.type === type).value
  return `${value('year')}-${value('month')}-${value('day')}`
}

export function contractPhase(record, today = damascusToday()) {
  if (['finish', 'current', 'future', 'unknown'].includes(record.planningPhase)) return record.planningPhase
  const start = record.startDate
  const end = record.endDate
  if (!start || !end || start > end) return 'unknown'
  if (start < today && end < today) return 'finish'
  if (start > today && end > today) return 'future'
  return 'current'
}
