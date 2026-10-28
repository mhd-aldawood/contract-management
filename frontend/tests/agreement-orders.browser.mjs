// Isolated UI regression checks: all API calls are mocked; no database records change.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const baseUrl = process.env.ORDER_TEST_URL || 'http://127.0.0.1:4175'
const output = process.env.ORDER_TEST_OUTPUT
const types = ['nafath-centers', 'lifelong-learning', 'educational-content', 'other-agreements', 'memorandum']
const endpoints = ['/api/nafath-center/', '/api/life-long/', '/api/educational-contents', '/api/other-agreement/', '/api/memorandum/']
const records = types.flatMap(feature => [1, 2, 3].map(id => ({ id, feature, key: `${feature}-${id}`,
  name: `اتفاقية ${feature} ${id}`, agreementNumber: `TEST-${feature}-${id}`, category: feature,
  hasFile: true, fileName: 'agreement.txt', orderCount: id === 1 ? 2 : id === 2 ? 0 : 1, isHidden: false,
  startDate: '2026-01-01', endDate: '2027-01-01', paymentSchedule: [], rows: [] })))
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
let checks = 0
try {
  for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
    for (const feature of [...types, 'planning', 'dean', 'finance']) {
      const context = await browser.newContext({ viewport, acceptDownloads: true })
      const page = await context.newPage()
      page.setDefaultTimeout(10000)
      const errors = []
      page.on('pageerror', error => errors.push(error.message))
      const permissions = Object.fromEntries([...types, 'planning', 'dean', 'finance'].map(code => [code, {
        read: types.includes(feature) ? types.includes(code) || code === 'planning' : code === feature, write: false, download: true,
      }]))
      const user = { id: 1, username: 'order-view-test', role: { code: feature }, permissions }
      await page.addInitScript(user => {
        localStorage.setItem('app_session', JSON.stringify(user))
        localStorage.setItem('access_token', 'mock-order-token')
      }, user)
      let delayed = false, fail = false, empty = false
      const orderRequests = []
      await page.route('**/api/**', async route => {
        const request = route.request()
        const url = new URL(request.url())
        let data = []
        if (url.pathname.endsWith('/auth/csrf/')) data = { csrfToken: 'mock-csrf' }
        else if (url.pathname.endsWith('/auth/token/refresh/')) data = { user, token: 'mock-order-token', csrfToken: 'mock-csrf' }
        else if (url.pathname.endsWith('/auth/me/')) data = user
        else if (url.pathname === '/api/files/grants/') {
          const grant = request.postDataJSON()
          assert.equal(grant.scope, ['planning', 'dean'].includes(feature) ? feature : 'agreement')
          data = { grant: 'single-use-grant', downloadUrl: baseUrl + '/api/files/download/' }
        } else if (url.pathname === '/api/files/download/') {
          assert.equal(request.headers()['x-download-grant'], 'single-use-grant')
          assert.equal(request.headers().authorization, 'Token mock-order-token')
          await route.fulfill({ contentType: 'application/octet-stream', body: 'test order file' }); return
        }
        else if (url.pathname.startsWith('/api/agreement-orders/')) {
          assert.equal(request.headers().authorization, 'Token mock-order-token')
          const [, , , kind, id] = url.pathname.split('/')
          const expectedScope = ['planning', 'dean'].includes(feature) ? feature : 'agreement'
          assert.equal(url.searchParams.get('scope'), expectedScope)
          orderRequests.push({ kind, id })
          if (url.pathname.endsWith('/file/')) {
            await route.fulfill({ contentType: 'application/octet-stream', body: 'test order file', headers: { 'Content-Disposition': 'attachment; filename="order.txt"' } })
            return
          }
          if (fail) {
            fail = false
            await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ status: 'FAILURE', message: 'تعذر تحميل أوامر الصرف' }) })
            return
          }
          if (delayed && id === '1') await new Promise(resolve => setTimeout(resolve, 450))
          data = empty ? [] : Array.from({ length: id === '1' ? 2 : 1 }, (_, index) => ({
            id: Number(id) * 10 + index, title: `${kind}-${id}-order-${index}`, fileName: 'order.txt',
            notes: 'ملاحظات المالية', fileSize: 15, uploadedBy: 'finance-test', createdAt: '2026-10-25T10:00:00Z',
          }))
        } else if (['/api/planning/agreements/', '/api/dean/agreements/', '/api/finance/agreements/'].includes(url.pathname)) data = records.map(record => ({ ...record }))
        else {
          const index = endpoints.indexOf(url.pathname)
          if (index >= 0) data = records.filter(record => record.feature === types[index]).map(record => ({ ...record }))
        }
        try { await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'SUCCESS', data, totalCount: data.length }) }) }
        catch (error) { if (!request.failure()) throw error }
      })

      await page.goto(baseUrl + (types.includes(feature) ? '/contracts/' + feature : '/' + feature))
      const firstKind = types.includes(feature) ? feature : types[0]
      const row = id => page.getByRole('row').filter({ hasText: `TEST-${firstKind}-${id}` })
      await row(2).waitFor()
      const filter = page.getByRole('combobox', { name: /^أوامر الصرف/ })
      await filter.selectOption('with')
      assert.equal(await row(2).count(), 0)
      await filter.selectOption('without')
      assert.equal(await row(1).count(), 0)
      await row(2).waitFor()
      if (feature !== 'finance') assert(await row(2).getByRole('button', { name: /عرض أوامر الصرف/ }).isDisabled())
      await page.getByRole('button', { name: 'إلغاء الفلاتر', exact: true }).click()
      assert.equal(await filter.inputValue(), '')
      await row(1).waitFor()
      if (types.includes(feature) || feature === 'planning') {
        await row(1).getByRole('button', { name: 'عرض التفاصيل', exact: true }).click()
        const details = page.getByRole('dialog')
        assert.equal(await details.locator('a[target="_blank"]').count(), 0)
        const attachmentDownload = page.waitForEvent('download')
        await details.getByRole('button', { name: 'تنزيل مرفق الاتفاقية', exact: true }).click()
        assert.equal((await attachmentDownload).suggestedFilename(), 'agreement.txt')
        await page.keyboard.press('Escape')
        await details.waitFor({ state: 'hidden' })
      }
      if (feature !== 'finance') {
        const button = id => row(id).getByRole('button', { name: /عرض أوامر الصرف/ })
        assert(await button(1).isEnabled())
        await button(1).click()
        const dialog = page.getByRole('dialog')
        await dialog.getByText(`${firstKind}-1-order-0`, { exact: true }).waitFor()
        assert.equal(await dialog.locator('.agreement-orders-table tbody tr').count(), 2)
        assert.equal(orderRequests[0].kind, firstKind)
        const downloadPromise = page.waitForEvent('download')
        await dialog.getByRole('button', { name: 'تنزيل', exact: true }).first().click()
        assert.equal((await downloadPromise).suggestedFilename(), 'order.txt')
        const box = await dialog.boundingBox()
        assert(box.x >= -1 && box.x + box.width <= viewport.width + 1)
        assert(box.y >= -1 && box.y + box.height <= viewport.height + 1)
        assert(viewport.width < 640 ? Math.round(box.width) === viewport.width : box.width >= 1100)
        assert(await dialog.locator('.base-modal__body').evaluate(element => element.scrollWidth <= element.clientWidth + 1), 'Modal content overflows horizontally')
        if (output && feature === 'nafath-centers') {
          await fs.mkdir(output, { recursive: true })
          await page.screenshot({ path: path.join(output, `agreement-orders-${viewport.width}.png`) })
        }
        await page.keyboard.press('Escape')
        await dialog.waitFor({ state: 'hidden' })
        assert.equal(await page.evaluate(() => document.body.classList.contains('modal-open')), false)

        if (feature === 'nafath-centers' && viewport.width === 1440) {
          delayed = true
          await button(1).click()
          await dialog.getByText('جارٍ تحميل أوامر الصرف…', { exact: true }).waitFor()
          await page.keyboard.press('Escape')
          await dialog.waitFor({ state: 'hidden' })
          await button(3).click()
          await dialog.getByText(`${firstKind}-3-order-0`, { exact: true }).waitFor()
          await page.waitForTimeout(550)
          assert.equal(await dialog.getByText(`${firstKind}-1-order-0`, { exact: true }).count(), 0)
          await page.keyboard.press('Escape')
          await dialog.waitFor({ state: 'hidden' })
          fail = true
          await button(3).click()
          await dialog.getByRole('alert').waitFor()
          await dialog.getByRole('button', { name: 'إعادة المحاولة', exact: true }).click()
          await dialog.getByText(`${firstKind}-3-order-0`, { exact: true }).waitFor()
          empty = true
          await dialog.getByRole('button', { name: 'تحديث القائمة', exact: true }).click()
          await dialog.getByText('لا توجد أوامر صرف حالية لهذه الاتفاقية.', { exact: true }).waitFor()
          await page.keyboard.press('Escape')
          await dialog.waitFor({ state: 'hidden' })
          assert(await button(3).isDisabled())
        }
      }
      assert.deepEqual(errors, [], feature + ': browser errors')
      await context.close()
      checks++
      console.log(`PASS: ${feature} filter${feature === 'finance' ? '' : ', disabled zero button, scoped modal and download'} at ${viewport.width}px`)
    }
  }
  console.log(`Passed ${checks} responsive page checks, including close/switch, retry and refreshed-zero behavior.`)
} finally { await browser.close() }
