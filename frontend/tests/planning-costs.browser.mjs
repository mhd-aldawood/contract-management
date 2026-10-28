import assert from 'node:assert/strict'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')

const base = process.env.PLANNING_TEST_URL || 'http://cm.localhost:81'
const types = ['nafath-centers', 'lifelong-learning', 'educational-content', 'other-agreements', 'memorandum']
const user = { id: 1, username: 'planning-cost-regression', isAdmin: true, role: { code: 'admin' }, permissions: {} }
const record = (id, changes = {}) => ({ id, key: `nafath-centers-${id}`, feature: 'nafath-centers', category: 'مراكز النفاذ',
  agreementNumber: 'COST-' + id, name: 'اتفاقية ' + id, subject: 'تفاصيل عمل ' + id, status: 'معتمدة',
  startDate: '2026-01-01', endDate: '2027-01-01', planningPhase: 'current', isHidden: false, orderCount: 0,
  paymentSchedule: [], costTable: [], ...changes })
const records = [
  record(1, { paymentMethod: 'table', costTable: [{ years: 'أول 5 سنوات', percentage: '40.00', details: 'تفاصيل الأولى' }] }),
  record(2, { paymentMethod: 'table', costTable: [{ years: 'سنة واحدة', percentage: '25.00', details: 'تفاصيل الثانية' }] }),
  record(3, { paymentMethod: 'text', paymentText: 'نص التكلفة المتفق عليها', costTable: [{ years: 'مسودة غير مختارة', percentage: '10' }] }),
  record(4, { estimatedCost: 0 }),
  record(5, { paymentMethod: 'table', paymentSchedule: [{ label: 'دفعة سابقة', amount: '250.00', dueDate: '2026-11-01' }] }),
  record(6, { paymentMethod: 'table' }),
]
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
try {
  for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport })
    const page = await context.newPage()
    const errors = [], writes = []
    page.on('pageerror', error => errors.push(error.message))
    await page.route('**/api/**', async route => {
      const request = route.request(), pathname = new URL(request.url()).pathname
      let data = []
      if (pathname.endsWith('/auth/csrf/')) data = { csrfToken: 'csrf' }
      else if (pathname.endsWith('/auth/token/refresh/')) data = { user, token: 'cost-regression-token', csrfToken: 'csrf' }
      else if (pathname.endsWith('/auth/me/')) data = user
      else if (pathname === '/api/planning/agreements/') data = records
      else if (request.method() === 'POST') {
        writes.push(request.postData())
        data = record(99)
      }
      await route.fulfill({ status: request.method() === 'POST' && !pathname.includes('/auth/') ? 201 : 200,
        contentType: 'application/json', body: JSON.stringify({ status: 'SUCCESS', message: 'تم الحفظ', data }) })
    })
    await page.goto(base + '/planning')
    const table = page.locator('.contract-list__table')
    await table.getByText('COST-1', { exact: true }).waitFor()
    for (const name of ['تفاصيل العمل', 'حالة الاتفاقية', 'التكلفة', 'تفاصيل التكلفة', 'نوع الاتفاقية']) {
      assert.equal(await table.getByRole('columnheader', { name, exact: true }).count(), 1)
    }
    const row = id => table.getByRole('row').filter({ hasText: 'COST-' + id })
    assert.equal(await row(3).getByRole('button', { name: 'إظهار الجدول', exact: true }).count(), 0)
    assert((await row(3).innerText()).includes('نص التكلفة المتفق عليها'))
    for (const id of [1, 2, 5, 6]) {
      await row(id).getByRole('button', { name: 'إظهار الجدول', exact: true }).click()
      const dialog = page.getByRole('dialog')
      await dialog.waitFor()
      if (id <= 2) {
        const expected = records[id - 1].costTable[0]
        for (const name of ['عدد السنوات', 'النسبة', 'تفاصيل']) assert.equal(await dialog.getByRole('columnheader', { name, exact: true }).count(), 1)
        await dialog.getByText(expected.details, { exact: true }).waitFor()
        assert.equal(await dialog.getByText(id === 1 ? 'تفاصيل الثانية' : 'تفاصيل الأولى', { exact: true }).count(), 0)
      } else if (id === 5) {
        await dialog.getByText('دفعة سابقة', { exact: true }).waitFor()
        assert.equal(await dialog.getByRole('columnheader', { name: 'المبلغ', exact: true }).count(), 1)
      } else await dialog.getByText('لا توجد صفوف تكلفة محفوظة لهذه الاتفاقية.').waitFor()
      assert(await dialog.locator('.base-modal__body').evaluate(element => element.scrollWidth <= element.clientWidth + 1))
      await page.keyboard.press('Escape')
      await dialog.waitFor({ state: 'hidden' })
    }
    for (const feature of types) {
      await page.goto(base + '/contracts/' + feature)
      await page.getByRole('button', { name: 'إضافة اتفاقية', exact: true }).click()
      const dialog = page.getByRole('dialog')
      await dialog.getByPlaceholder('أدخل رقم الاتفاقية').fill('COST-NEW')
      await dialog.getByPlaceholder('أدخل اسم الاتفاقية').fill('اتفاقية اختبار التكلفة')
      await dialog.getByLabel('بداية الاتفاقية', { exact: false }).fill('2026-01-01')
      await dialog.getByLabel('نهاية الاتفاقية', { exact: false }).fill('2027-01-01')
      if (!['other-agreements', 'memorandum'].includes(feature)) {
        await dialog.getByLabel('اسم الشركة', { exact: false }).fill('جهة اختبار')
        await dialog.getByLabel('موضوع الاتفاقية', { exact: false }).fill('تفاصيل العمل الاختبارية')
        await dialog.getByLabel('حالة الاتفاقية', { exact: false }).fill('معتمدة')
      }
      await dialog.locator('.payment-section select').selectOption('table')
      assert(await dialog.getByRole('button', { name: 'حفظ الاتفاقية', exact: true }).isDisabled())
      await dialog.getByRole('button', { name: 'إضافة صف', exact: false }).click()
      await dialog.getByLabel('عدد السنوات', { exact: true }).fill('أول 5 سنوات')
      await dialog.getByLabel('النسبة', { exact: true }).fill('120')
      assert(await dialog.getByRole('button', { name: 'حفظ الاتفاقية', exact: true }).isDisabled())
      await dialog.getByLabel('النسبة', { exact: true }).fill('40')
      await dialog.getByLabel('تفاصيل', { exact: true }).fill('تفاصيل النسبة لهذا العقد')
      assert(await dialog.locator('.base-modal__body').evaluate(element => element.scrollWidth <= element.clientWidth + 1))
      await dialog.getByRole('button', { name: 'حفظ الاتفاقية', exact: true }).click()
      await dialog.waitFor({ state: 'hidden' })
      const body = writes.at(-1)
      assert(body.includes('name="costTable"'), feature + ': missing costTable in multipart payload')
      assert(/"percentage":(?:"40"|40)/.test(body), feature + ': percentage was not serialized as a row')
      assert(body.includes('أول 5 سنوات'))
    }
    assert.deepEqual(errors, [])
    console.log(`PASS: Planning columns, text/table/legacy/empty cost display, per-document rows and all five cost forms at ${viewport.width}px`)
    await context.close()
  }
} finally { await browser.close() }
