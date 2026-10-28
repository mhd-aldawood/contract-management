import { test } from 'node:test'
import assert from 'node:assert/strict'
import { costText, hasCostTable, validCostTable, workDetails } from '../src/presentation/utils/agreementCosts.js'

test('the saved text/table selection controls Planning cost display', () => {
  assert.equal(hasCostTable({ paymentMethod: 'table', costTable: [] }), true)
  assert.equal(hasCostTable({ paymentMethod: 'text', costTable: [{ years: '1' }] }), false)
  assert.equal(costText({ paymentMethod: 'text', paymentText: 'نص التكلفة', estimatedCost: 100 }), 'نص التكلفة')
  assert.notEqual(costText({ estimatedCost: 0 }), '—')
  assert.equal(costText({}), '—')
})
test('year/percentage rows require real input and allow zero percent', () => {
  const form = { paymentMethod: 'table', costTable: [{ years: 'أول 5 سنوات', percentage: '0', details: '' }] }
  assert.equal(validCostTable(form), true)
  for (const percentage of ['', null, '-1', '101', 'NaN', '1.234']) {
    assert.equal(validCostTable({ ...form, costTable: [{ ...form.costTable[0], percentage }] }), false)
  }
  assert.equal(validCostTable({ paymentMethod: 'table', costTable: [] }), false)
  assert.equal(validCostTable({ paymentMethod: 'text', costTable: [] }), true)
})
test('work details use saved subject or clauses without fabricated content', () => {
  assert.equal(workDetails({ subject: 'العمل', rows: [{ body: 'بند' }] }), 'العمل')
  assert.equal(workDetails({ rows: [{ header: 'بند', body: 'تفاصيل' }] }), 'بند: تفاصيل')
  assert.equal(workDetails({}), '—')
})
