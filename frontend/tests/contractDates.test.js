import assert from 'node:assert/strict'
import test from 'node:test'
import { contractPhase, damascusToday, formatContractDate } from '../src/presentation/utils/contractDates.js'

const today = '2026-10-25'

test('agreement phase follows both dates and includes today in current', () => {
  const cases = [
    ['2026-10-01', '2026-10-24', 'finish'],
    ['2026-10-01', '2026-11-01', 'current'],
    ['2026-10-26', '2026-11-01', 'future'],
    [today, '2026-11-01', 'current'],
    ['2026-10-01', today, 'current'],
    [today, today, 'current'],
    [null, '2026-11-01', 'unknown'],
    ['2026-10-01', null, 'unknown'],
    ['2026-11-01', '2026-10-01', 'unknown'],
  ]
  for (const [startDate, endDate, expected] of cases) {
    assert.equal(contractPhase({ startDate, endDate, status: 'ignored manual status' }, today), expected)
  }
})

test('Planning uses the backend classification rather than the browser clock', () => {
  assert.equal(contractPhase({ startDate: '2026-10-01', endDate: '2026-11-01', planningPhase: 'finish' }, today), 'finish')
})

test('today follows Damascus at its midnight boundary', () => {
  assert.equal(damascusToday(new Date('2026-10-24T20:59:59Z')), '2026-10-24')
  assert.equal(damascusToday(new Date('2026-10-24T21:00:00Z')), '2026-10-25')
})

test('missing dates display a placeholder', () => {
  assert.equal(formatContractDate(null), '—')
})
