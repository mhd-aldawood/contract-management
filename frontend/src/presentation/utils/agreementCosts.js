export function hasCostTable(record) {
  return record.paymentMethod === 'table' || (!record.paymentMethod && record.costTable?.length > 0)
}

export function costText(record) {
  if (record.paymentMethod === 'text' && record.paymentText?.trim()) return record.paymentText
  if (record.estimatedCost !== null && record.estimatedCost !== undefined && record.estimatedCost !== '') {
    const value = Number(record.estimatedCost)
    if (Number.isFinite(value)) return new Intl.NumberFormat('ar-SY', { maximumFractionDigits: 2 }).format(value)
  }
  return '—'
}

export function workDetails(record) {
  return record.subject || record.contractText || (record.rows || []).map(row => [row.header, row.body].filter(Boolean).join(': ')).filter(Boolean).join('\n') || '—'
}

export function validCostTable(form) {
  if (form.paymentMethod !== 'table') return true
  const rows = form.costTable
  return Array.isArray(rows) && rows.length > 0 && rows.length <= 100 && rows.every(row =>
    String(row.years || '').trim().length > 0 && String(row.years).length <= 120 &&
    row.percentage !== '' && row.percentage != null && Number.isFinite(Number(row.percentage)) &&
    Number(row.percentage) >= 0 && Number(row.percentage) <= 100 &&
    /^\d+(\.\d{1,2})?$/.test(String(row.percentage)) && String(row.details || '').length <= 2000)
}
