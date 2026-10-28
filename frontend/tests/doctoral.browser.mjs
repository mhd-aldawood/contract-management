// Local Docker integration: creates its own contracts and removes their records/files afterward.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.DASHBOARD_TEST_URL || 'http://cm.localhost:81'
assert(['localhost', '127.0.0.1', 'cm.localhost'].includes(new URL(base).hostname))
const accounts = JSON.parse(await fs.readFile(process.env.DASHBOARD_TEST_ACCOUNTS, 'utf8'))
const admin = accounts.find(account => account.role === 'admin')
const numbers = []
const prefix = 'PHD-REG-' + randomUUID().slice(0, 8) + '-'
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
async function signIn(page, account) {
  await page.goto(base + '/login')
  await page.getByLabel('اسم المستخدم').fill(account.username)
  await page.getByLabel('كلمة المرور', { exact: true }).fill(account.password)
  await page.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click()
  await page.locator('.dashboard-stats').waitFor()
}
try {
  for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport, acceptDownloads: true })
    const page = await context.newPage()
    page.setDefaultTimeout(15000)
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    await signIn(page, admin)
    if (viewport.width < 768) await page.getByRole('button', { name: 'فتح القائمة', exact: true }).click()
    const names = await page.locator('.nav-link').allTextContents()
    const educationalIndex = names.findIndex(name => name.includes('المحتوى التعليمي'))
    assert(educationalIndex >= 0 && names[educationalIndex + 1].includes('عقد الدكتوراه'))
    await page.getByRole('button', { name: 'عقد الدكتوراه', exact: false }).click()
    await page.getByRole('heading', { name: 'عقد الدكتوراه', exact: true }).waitFor()
    await page.getByRole('button', { name: 'إضافة عقد', exact: true }).click()
    const dialog = page.getByRole('dialog')
    assert(await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).isDisabled())
    const number = prefix + viewport.width
    numbers.push(number)
    await dialog.getByLabel('رقم العقد', { exact: false }).fill(number)
    await dialog.getByLabel('اسم الدكتور', { exact: false }).fill('الدكتور اختبار محلي')
    await dialog.getByLabel('المهام', { exact: false }).fill('الإشراف على الرسائل وتدريس المقررات')
    await dialog.getByLabel('رتبة الدكتور', { exact: false }).fill('أستاذ مساعد')
    await dialog.getByLabel('مدة العقد', { exact: false }).fill('سنة دراسية واحدة')
    await dialog.getByLabel('أمر المباشرة', { exact: false }).fill('أمر مباشرة رقم 21')
    await dialog.getByLabel('وثيقة العقد', { exact: false }).setInputFiles({ name: 'doctoral-document.txt', mimeType: 'text/plain', buffer: Buffer.from('Doctoral contract regression document') })
    assert(await dialog.locator('.base-modal__body').evaluate(element => element.scrollWidth <= element.clientWidth + 1))
    if (process.env.DOCTORAL_TEST_OUTPUT) {
      await fs.mkdir(process.env.DOCTORAL_TEST_OUTPUT, { recursive: true })
      await dialog.locator('.base-modal__body').evaluate(element => { element.scrollTop = 0 })
      await page.screenshot({ path: process.env.DOCTORAL_TEST_OUTPUT + `/doctoral-${viewport.width}.png`, animations: 'disabled' })
    }
    const saved = page.waitForResponse(response => response.url().endsWith('/api/doctoral-contracts/') && response.request().method() === 'POST')
    await dialog.getByRole('button', { name: 'حفظ العقد', exact: true }).click()
    const response = await saved
    assert.equal(response.status(), 201, JSON.stringify(await response.json()))
    const contract = (await response.json()).data
    assert.equal(contract.contractNumber, number)
    assert.equal(contract.fileName, 'doctoral-document.txt')
    assert(!JSON.stringify(contract).includes('/media/'))
    await dialog.waitFor({ state: 'hidden' })
    await page.getByRole('searchbox', { name: 'البحث', exact: true }).fill(number)
    const row = page.locator('.contract-list__table tbody tr').filter({ hasText: number })
    for (const text of ['الدكتور اختبار محلي', 'أستاذ مساعد', 'سنة دراسية واحدة', 'أمر مباشرة رقم 21']) assert((await row.innerText()).includes(text))
    await row.getByRole('button', { name: 'عرض التفاصيل', exact: true }).click()
    await dialog.getByText('الإشراف على الرسائل وتدريس المقررات', { exact: true }).waitFor()
    const download = page.waitForEvent('download')
    await dialog.getByRole('button', { name: 'تنزيل الوثيقة', exact: true }).click()
    assert.equal((await download).suggestedFilename(), 'doctoral-document.txt')
    await page.keyboard.press('Escape')
    await dialog.waitFor({ state: 'hidden' })
    await page.reload()
    await page.getByRole('heading', { name: 'عقد الدكتوراه', exact: true }).waitFor()
    assert.deepEqual(errors, [])
    console.log(`PASS: doctoral sidebar, six-field form, document upload, persistence, list/details and private download at ${viewport.width}px`)
    await context.close()
  }
  for (const account of accounts.filter(account => account.role !== 'admin')) {
    const context = await browser.newContext()
    const page = await context.newPage()
    await signIn(page, account)
    await page.goto(base + '/contracts/doctoral-contracts')
    await page.getByRole('heading', { name: 'عقد الدكتوراه', exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: 'إضافة عقد', exact: true }).count(), account.role === 'contract' ? 1 : 0)
    console.log('PASS: doctoral access for ' + account.role)
    await context.close()
  }
} finally {
  await browser.close()
  if (numbers.length) execFileSync('docker', ['compose', 'exec', '-T', '-e', 'CM_DOCTORAL_TEST_NUMBERS=' + JSON.stringify(numbers),
    'backend', 'python', 'manage.py', 'shell', '-c', "import os,json; from contract.doctoral_models import DoctoralContract; numbers=json.loads(os.environ['CM_DOCTORAL_TEST_NUMBERS']); assert 0<len(numbers)<=2 and all(number.startswith('PHD-REG-') for number in numbers); records=list(DoctoralContract.objects.filter(agreement_number__in=numbers)); [record.file.delete(save=False) for record in records if record.file]; DoctoralContract.objects.filter(pk__in=[record.pk for record in records]).delete()"], { stdio: 'pipe' })
}
