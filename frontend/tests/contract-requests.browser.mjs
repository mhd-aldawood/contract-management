import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.DASHBOARD_TEST_URL || 'http://cm.localhost:81'
assert(['localhost', '127.0.0.1', 'cm.localhost'].includes(new URL(base).hostname))
const accounts = JSON.parse(await fs.readFile(process.env.DASHBOARD_TEST_ACCOUNTS, 'utf8'))
const admin = accounts.find(account => account.role === 'admin')
const prefix = 'REQUEST-REG-' + randomUUID() + '-'
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
async function login(page, account) {
  await page.goto(base + '/login')
  await page.getByLabel('اسم المستخدم').fill(account.username)
  await page.getByLabel('كلمة المرور', { exact: true }).fill(account.password)
  await page.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click()
  await page.locator('.dashboard-stats').waitFor()
}
try {
  for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport })
    const page = await context.newPage()
    page.setDefaultTimeout(15000)
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await login(page, admin)
    if (viewport.width < 768) await page.getByRole('button', { name: 'فتح القائمة', exact: true }).click()
    await page.getByRole('button', { name: 'إضافة عقد', exact: true }).click()
    await page.getByRole('heading', { name: 'إضافة عقد', exact: true }).waitFor()
    await page.getByRole('button', { name: 'إضافة عقد جديد', exact: true }).click()
    const dialog = page.getByRole('dialog')
    assert(await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).isDisabled())
    const memo = prefix + viewport.width
    await dialog.getByLabel('مذكرة تبريرية', { exact: false }).fill(memo)
    await dialog.getByLabel('دفتر شروط فني', { exact: false }).fill('الشروط الفنية للعقد')
    await dialog.getByLabel('دفتر شروط حقوقي', { exact: false }).fill('الشروط الحقوقية للعقد')
    await dialog.getByLabel('تاريخ التذكير', { exact: false }).fill('2026-11-03')
    await dialog.getByLabel('تمت المناقصة بنجاح', { exact: true }).check()
    await dialog.getByLabel('تاريخ الإعلان (بداية)', { exact: false }).fill('2026-11-01')
    await dialog.getByLabel('تاريخ الإعلان (نهاية)', { exact: false }).fill('2026-10-01')
    assert(await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).isDisabled())
    await dialog.getByLabel('تاريخ الإعلان (نهاية)', { exact: false }).fill('2026-11-15')
    await dialog.getByRole('button', { name: 'إضافة محضر', exact: true }).click()
    await dialog.getByRole('button', { name: 'إضافة محضر', exact: true }).click()
    await dialog.getByRole('button', { name: 'حذف المحضر 3', exact: true }).click()
    for (let i = 0; i < 2; i++) {
      const row = dialog.locator('.request-row').nth(i)
      await row.getByLabel('رقم المحضر', { exact: true }).fill('MIN-' + (i + 1))
      await row.getByLabel('التاريخ', { exact: true }).fill('2026-11-02')
      await row.getByLabel('الموضوع', { exact: true }).fill('موضوع محضر ' + (i + 1))
    }
    await dialog.getByRole('button', { name: 'إضافة رغبة جديدة', exact: true }).click()
    await dialog.getByRole('button', { name: 'إضافة رغبة جديدة', exact: true }).click()
    await dialog.getByRole('button', { name: 'حذف الرغبة 2', exact: true }).click()
    await dialog.getByLabel('الرغبة 1', { exact: true }).fill('رغبة محفوظة لهذا العقد')
    await dialog.getByLabel('فشلت المناقصة', { exact: true }).check()
    assert.equal(await dialog.locator('.request-row').count(), 0)
    assert(await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).isEnabled())
    await dialog.getByLabel('تمت المناقصة بنجاح', { exact: true }).check()
    assert.equal(await dialog.locator('.request-row').count(), 2)
    assert.equal(await dialog.getByLabel('تاريخ الإعلان (نهاية)', { exact: false }).inputValue(), '2026-11-15')
    assert(await dialog.locator('.base-modal__body').evaluate(element => element.scrollWidth <= element.clientWidth + 1))
    if (process.env.REQUEST_TEST_OUTPUT) {
      await fs.mkdir(process.env.REQUEST_TEST_OUTPUT, { recursive: true })
      await dialog.locator('.base-modal__body').evaluate(element => { element.scrollTop = 0 })
      await page.screenshot({ path: process.env.REQUEST_TEST_OUTPUT + `/contract-request-${viewport.width}.png`, animations: 'disabled' })
    }
    const saved = page.waitForResponse(response => response.url().endsWith('/api/contract-requests/') && response.request().method() === 'POST')
    await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).click()
    const response = await saved
    assert.equal(response.status(), 201)
    const data = (await response.json()).data
    assert.equal(data.reminderDate, '2026-11-03')
    assert.equal(data.bids.length, 2)
    assert.deepEqual(data.wishes, ['رغبة محفوظة لهذا العقد'])
    await dialog.waitFor({ state: 'hidden' })
    await page.getByRole('searchbox', { name: 'البحث', exact: true }).fill(memo)
    const row = page.locator('.requests-table tbody tr').filter({ hasText: memo })
    await row.getByRole('button', { name: 'عرض التفاصيل', exact: true }).click()
    await dialog.getByText('رغبة محفوظة لهذا العقد', { exact: true }).waitFor()
    await dialog.getByText('MIN-2', { exact: true }).waitFor()
    await page.keyboard.press('Escape')
    await dialog.waitFor({ state: 'hidden' })
    await row.getByRole('button', { name: 'تعديل', exact: true }).click()
    assert.equal(await dialog.getByLabel('مذكرة تبريرية', { exact: false }).inputValue(), memo)
    await dialog.getByLabel('فشلت المناقصة', { exact: true }).check()
    const updated = page.waitForResponse(response => response.url().endsWith(`/api/contract-requests/${data.id}/`) && response.request().method() === 'PATCH')
    await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).click()
    const update = await updated
    assert.equal(update.status(), 200)
    const failed = (await update.json()).data
    assert.equal(failed.announceStart, null)
    assert.deepEqual(failed.bids, [])
    assert.deepEqual(failed.wishes, [])
    assert.equal(failed.reminderDate, '2026-11-03')
    await dialog.waitFor({ state: 'hidden' })
    await page.getByRole('combobox', { name: 'حالة المناقصة', exact: true }).selectOption('success')
    assert.equal(await row.count(), 0)
    await page.getByRole('combobox', { name: 'حالة المناقصة', exact: true }).selectOption('failed')
    await row.waitFor()
    await page.reload()
    await row.waitFor()
    await row.getByRole('button', { name: 'حذف', exact: true }).click()
    let rejectDelete = true
    await page.route('**/api/contract-requests/' + data.id + '/', async route => {
      if (route.request().method() === 'DELETE' && rejectDelete) {
        rejectDelete = false
        await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ status: 'FAILURE', message: 'تعذر الحذف مؤقتاً' }) })
      } else await route.continue()
    })
    await dialog.getByRole('button', { name: 'تأكيد الحذف', exact: true }).click()
    await dialog.getByRole('alert').waitFor()
    await dialog.getByRole('button', { name: 'تأكيد الحذف', exact: true }).click()
    await dialog.waitFor({ state: 'hidden' })
    await row.waitFor({ state: 'hidden' })
    assert.deepEqual(errors, [])
    console.log(`PASS: create-contract fields, dynamic rows, reminder persistence, success/failed transition, filters, edit/delete and responsive modal at ${viewport.width}px`)
    await context.close()
  }
  for (const account of accounts.filter(account => account.role !== 'admin')) {
    const context = await browser.newContext()
    const page = await context.newPage()
    await login(page, account)
    await page.goto(base + '/contracts/create')
    await page.getByRole('heading', { name: 'إضافة عقد', exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: 'إضافة عقد جديد', exact: true }).count(), account.role === 'contract' ? 1 : 0)
    console.log('PASS: create-contract role access for ' + account.role)
    await context.close()
  }
} finally {
  await browser.close()
  execFileSync('docker', ['compose', 'exec', '-T', '-e', 'CM_REQUEST_TEST_PREFIX=' + prefix, 'backend', 'python', 'manage.py', 'shell', '-c',
    "import os; from contract.request_models import ContractRequest; prefix=os.environ['CM_REQUEST_TEST_PREFIX']; assert prefix.startswith('REQUEST-REG-') and len(prefix)>45; ContractRequest.objects.filter(justification_memo__startswith=prefix).delete()"], { stdio: 'pipe' })
}
