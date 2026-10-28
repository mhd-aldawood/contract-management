// Run against a Vite preview with Playwright and Chrome available.
// All API traffic is intercepted; this check never changes database records.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const baseUrl = process.env.MODAL_TEST_URL || 'http://127.0.0.1:4173'
const output = process.env.MODAL_TEST_OUTPUT
const featureCodes = ['home', 'planning', 'finance', 'dean', 'nafath-centers', 'memorandum',
  'lifelong-learning', 'other-agreements', 'educational-content', 'profile', 'settings', 'about', 'access-control', 'user-management']
const permissions = Object.fromEntries(featureCodes.map(code => [code, { read: true, write: true }]))
const admin = { id: 1, username: 'layout-test', isAdmin: true, role: { code: 'admin', name: 'Admin' }, permissions }
const matrix = {
  features: featureCodes.map(code => ({ code, nameAr: `ميزة ${code}` })),
  roles: [{ code: 'admin', name: 'Admin', permissions }, { code: 'contract', name: 'العقود', permissions }],
}
const record = { id: 1, name: 'اتفاقية اختبار العرض', agreementNumber: 'LAYOUT-1', companyName: 'جهة الاختبار',
  startDate: '2026-10-01', endDate: '2027-10-01', reminderDate: '2027-09-01', rows: [], paymentSchedule: [] }
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
let checks = 0
try {
  for (const viewport of [{ width: 1440, height: 960 }, { width: 768, height: 1024 }, { width: 390, height: 844 }, { width: 320, height: 640 }, { width: 844, height: 390 }]) {
    const context = await browser.newContext({ viewport })
    const page = await context.newPage()
    page.setDefaultTimeout(8000)
    const errors = []
    const writes = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', message => {
      if (message.type() === 'error' || (message.type() === 'warning' && /teleport|target|unhandled/i.test(message.text()))) errors.push(message.text())
    })
    await page.addInitScript(user => {
      localStorage.setItem('app_session', JSON.stringify(user))
      localStorage.setItem('access_token', 'isolated-layout-test')
    }, admin)
    await page.route('**/api/**', async route => {
      const request = route.request()
      const pathname = new URL(request.url()).pathname
      let data = []
      if (pathname.endsWith('/auth/csrf/')) data = { csrfToken: 'mock-csrf' }
      else if (pathname.endsWith('/auth/token/refresh/')) data = { user: admin, token: 'isolated-layout-test', csrfToken: 'mock-csrf' }
      else if (pathname.endsWith('/auth/me/')) data = admin
      else if (pathname.endsWith('/auth/access-control/')) data = matrix
      else if (pathname.endsWith('/auth/users/')) data = [{ id: 2, username: 'sample-user', role: matrix.roles[1], isActive: true }]
      else if (request.method() === 'GET') data = [record]
      else { writes.push({ pathname, body: request.postData() }); data = record }
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'SUCCESS', code: 'request.success', data, totalCount: Array.isArray(data) ? data.length : 1 }) })
    })

    async function assertLayout(label, large = false) {
      const dialog = page.getByRole('dialog')
      await dialog.waitFor()
      await page.waitForTimeout(200) // Let the opening transition finish before measuring.
      const metrics = await dialog.evaluate(element => {
        const rect = element.getBoundingClientRect()
        const body = element.querySelector('.base-modal__body')
        const footer = element.querySelector('.base-modal__footer').getBoundingClientRect()
        const nestedScrollers = [...body.querySelectorAll('*')].filter(child =>
          !['TEXTAREA', 'INPUT', 'SELECT'].includes(child.tagName) &&
          ['auto', 'scroll'].includes(getComputedStyle(child).overflowY) && child.scrollHeight > child.clientHeight + 1)
        const controls = [...element.querySelectorAll('input:not([type=hidden]), select, textarea, button')].filter(child => child.getClientRects().length && !child.closest('[hidden]'))
        return { width: rect.width, left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom,
          footerTop: footer.top, footerBottom: footer.bottom, horizontalOverflow: body.scrollWidth - body.clientWidth,
          nestedScrollers: nestedScrollers.length,
          clippedControls: controls.filter(child => { const r = child.getBoundingClientRect(); return r.left < rect.left - 1 || r.right > rect.right + 1 }).length }
      })
      assert(metrics.left >= -1 && metrics.right <= viewport.width + 1, `${label}: dialog outside viewport`)
      assert(metrics.top >= -1 && metrics.bottom <= viewport.height + 1, `${label}: dialog too tall`)
      assert(metrics.footerTop >= 0 && metrics.footerBottom <= viewport.height + 1, `${label}: footer inaccessible`)
      assert(metrics.horizontalOverflow <= 1, `${label}: horizontal form overflow`)
      assert.equal(metrics.clippedControls, 0, `${label}: clipped form controls`)
      assert.equal(metrics.nestedScrollers, 0, `${label}: nested vertical scrolling`)
      if (viewport.width >= 1200 && large) assert(metrics.width >= 1100, `${label}: large dialog still narrow`)
      if (viewport.width <= 640) assert.equal(Math.round(metrics.width), viewport.width, `${label}: phone dialog not full width`)
      checks++
    }

    for (const feature of ['nafath-centers', 'lifelong-learning', 'educational-content', 'other-agreements', 'memorandum']) {
      await page.goto(`${baseUrl}/contracts/${feature}`)
      await page.getByRole('button', { name: 'إضافة اتفاقية', exact: true }).click()
      const dialog = page.getByRole('dialog')
      await dialog.getByPlaceholder('أدخل رقم الاتفاقية').waitFor()
      await assertLayout(feature, true)
      assert.equal(await dialog.locator('.base-modal__footer').getByRole('button', { name: 'حفظ الاتفاقية', exact: true }).count(), 1)
      if (feature === 'nafath-centers') {
        await dialog.getByLabel('طريقة الدفع', { exact: false }).selectOption('table')
        await dialog.getByRole('button', { name: 'إضافة صف' }).click()
        await dialog.getByRole('button', { name: 'إضافة صف' }).click()
        await assertLayout('payment schedule', true)
        await dialog.getByRole('button', { name: 'حذف صف التكلفة 2', exact: true }).click()
        assert.equal(await dialog.locator('.payment-row').count(), 1)
        await dialog.getByLabel('عدد السنوات', { exact: true }).fill('أول 5 سنوات')
        await dialog.getByLabel('النسبة', { exact: true }).fill('40')
        await dialog.getByLabel('تفاصيل', { exact: true }).fill('تفاصيل التكلفة')
        if (output && [1440, 390].includes(viewport.width)) {
          await fs.mkdir(output, { recursive: true })
          await page.screenshot({ path: path.join(output, `agreement-${viewport.width}.png`) })
        }
        await dialog.getByLabel('رقم الاتفاقية', { exact: false }).fill('LAYOUT-NEW')
        await dialog.getByLabel('اسم الاتفاقية', { exact: false }).fill('اتفاقية اختبار')
        await dialog.getByLabel('اسم الشركة', { exact: false }).fill('جهة اختبار')
        await dialog.getByLabel('موضوع الاتفاقية', { exact: false }).fill('موضوع الاختبار')
        await dialog.getByLabel('الكلفة التقديرية', { exact: false }).fill('100')
        await dialog.getByLabel('بداية الاتفاقية', { exact: false }).fill('2026-10-01')
        await dialog.getByLabel('نهاية الاتفاقية', { exact: false }).fill('2027-10-01')
        await dialog.getByLabel('حالة الاتفاقية', { exact: false }).fill('نشط')
        await dialog.getByLabel('طريقة الدفع', { exact: false }).selectOption('text')
        await dialog.getByLabel('تفاصيل وشروط الدفع').fill('دفعة واحدة')
        await dialog.getByRole('button', { name: 'حفظ الاتفاقية', exact: true }).click()
        await dialog.waitFor({ state: 'hidden' })
        assert(writes.some(request => request.pathname.includes('nafath-center/create') && request.body.includes('LAYOUT-NEW')), 'Footer Save did not submit the agreement')
      } else {
        await dialog.getByRole('button', { name: 'إغلاق النافذة' }).click()
        await dialog.waitFor({ state: 'hidden' })
      }
      await page.getByRole('button', { name: 'عرض التفاصيل', exact: true }).click()
      await assertLayout(`${feature} details`, true)
      await page.keyboard.press('Escape')
      await dialog.waitFor({ state: 'hidden' })
      assert.equal(await page.evaluate(() => document.body.classList.contains('modal-open')), false, 'Body remained locked')
    }

    await page.goto(`${baseUrl}/admin/users`)
    await page.getByRole('button', { name: 'إضافة مستخدم', exact: false }).click()
    await assertLayout('user create')
    await page.getByRole('dialog').getByLabel('الدور', { exact: false }).selectOption('contract')
    await page.locator('.permission-preview summary').click()
    await assertLayout('user role permissions expanded')
    if (output && viewport.width === 1440) await page.screenshot({ path: path.join(output, 'user-permissions-1440.png') })
    await page.keyboard.press('Escape')
    await page.getByRole('dialog').waitFor({ state: 'hidden' })
    await page.getByRole('button', { name: 'تعديل', exact: true }).click()
    await assertLayout('user edit')
    await page.keyboard.press('Escape')
    await page.goto(`${baseUrl}/admin/roles`)
    await page.getByRole('button', { name: 'إضافة دور', exact: false }).click()
    await assertLayout('role create')
    await page.keyboard.press('Escape')
    await page.getByRole('dialog').waitFor({ state: 'hidden' })
    await page.getByLabel('الدور المراد إدارته').selectOption('contract')
    await page.getByRole('button', { name: 'تعديل الاسم' }).click()
    await assertLayout('role edit')
    assert.deepEqual(errors, [], `Browser errors at ${viewport.width}px`)
    await context.close()
    console.log(`PASS: agreement creation/details, payments, users and roles at ${viewport.width} × ${viewport.height}`)
  }
  console.log(`Passed ${checks} responsive dialog checks; footer Save submitted successfully at every viewport.`)
} finally {
  await browser.close()
}
