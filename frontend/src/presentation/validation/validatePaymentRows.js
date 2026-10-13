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