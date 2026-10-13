
import { paymentRowSchema } from './paymentRowSchema'
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