// Live local verification. Credentials are read from a temporary file, never committed.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const accounts = JSON.parse(await fs.readFile(process.env.DASHBOARD_TEST_ACCOUNTS, 'utf8'))
const baseUrl = process.env.DASHBOARD_TEST_URL || 'http://cm.localhost:81'
const output = process.env.DASHBOARD_TEST_OUTPUT
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
const expected = {
  admin: ['المستخدمون الفعالون', 'الأدوار', 'أوامر الصرف'],
  dean: ['المستخدمون', 'مخفية عن التخطيط'],
  finance: ['أوامر الصرف', 'اتفاقيات دون أمر صرف', 'أوامر مضافة هذا الشهر'],
  contract: ['اتفاقيات جديدة هذا الشهر', 'تذكيرات مستحقة'],
  planning: ['اتفاقيات حالية', 'اتفاقيات مستقبلية'],
}
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    for (const account of accounts) {
      const context = await browser.newContext({ viewport })
      const page = await context.newPage()
      page.setDefaultTimeout(15000)
      const errors = []
      page.on('pageerror', error => errors.push(error.message))
      await page.goto(baseUrl + '/login')
      await page.getByLabel('اسم المستخدم').fill(account.username)
      await page.getByLabel('كلمة المرور', { exact: true }).fill(account.password)
      const loginPromise = page.waitForResponse(response => response.url().includes('/api/auth/login/'))
      const responsePromise = page.waitForResponse(response => response.url().includes('/api/dashboard/'))
      await page.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click()
      let accessToken = (await (await loginPromise).json()).data.token
      const response = await responsePromise
      assert.equal(response.status(), 200, account.role + ': dashboard HTTP failure')
      const data = (await response.json()).data
      assert.equal(data.mode, account.role)
      await page.getByRole('heading', { name: 'لوحة التحكم', exact: true }).waitFor()
      await page.locator('.dashboard-stats').waitFor()
      for (const label of expected[account.role]) assert.equal(await page.locator('.dashboard-stats').getByRole('heading', { name: label, exact: true }).count(), 1)
      if (account.role === 'planning') {
        assert.equal(data.agreements.hidden, 0)
        assert.equal(data.finance, null)
        assert.equal(data.users, null)
      }
      if (['finance', 'contract', 'planning'].includes(account.role)) assert.equal(data.users, null)
      assert.equal(await page.locator('.dashboard-type-bar').count(), data.charts.types.length)
      assert.equal(await page.locator('.dashboard-month').count(), 6)
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)
      assert(overflow <= 1, account.role + ': dashboard overflows at ' + viewport.width)
      assert.equal(await page.locator('.dashboard-shortcuts a[href="/admin/users"]').count(), account.role === 'admin' ? 1 : 0)
      const statsText = await page.locator('.dashboard-stats').innerText()
      const refreshed = page.waitForResponse(response => response.url().includes('/api/dashboard/'))
      await page.getByRole('button', { name: 'تحديث البيانات', exact: true }).click()
      assert.equal((await refreshed).status(), 200)
      await page.getByRole('button', { name: 'تحديث البيانات', exact: true }).waitFor()
      assert.equal(await page.locator('.dashboard-stats').innerText(), statsText)
      if (output) {
        await fs.mkdir(output, { recursive: true })
        await page.screenshot({ path: path.join(output, account.role + '-' + viewport.width + '.png') })
      }
      if (data.recentAgreements.length) {
        const record = data.recentAgreements[0]
        await page.getByRole('link', { name: 'فتح الاتفاقية', exact: false }).first().click()
        if (['admin', 'dean'].includes(account.role)) {
          await page.locator('#dean-review .dean-details').waitFor()
          assert.equal(await page.locator('.dean-selector select').inputValue(), record.key)
        } else if (account.role === 'finance') {
          await page.waitForFunction(key => document.querySelector('.finance-document-selector select')?.value === key, record.key)
          assert.equal(await page.locator('.finance-document-selector select').inputValue(), record.key)
        } else {
          assert.equal(await page.getByRole('searchbox', { name: 'البحث', exact: true }).inputValue(), record.agreementNumber)
        }
      }
      await page.goto(baseUrl + '/home')
      await page.locator('.dashboard-stats').waitFor()
      const renewed = page.waitForResponse(response => response.url().includes('/api/auth/token/refresh/'))
      await page.reload()
      const renewal = await renewed
      assert.equal(renewal.status(), 200, account.role + ': reload session renewal failed')
      accessToken = (await renewal.json()).data.token
      await page.locator('.dashboard-stats').waitFor()
      const credentials = await page.evaluate(() => ['localStorage', 'sessionStorage'].flatMap(storage => ['access_token', 'refresh_token', 'app_session', 'app_users'].filter(key => window[storage].getItem(key))))
      assert.deepEqual(credentials, [], account.role + ': credentials persisted in browser storage')
      const cookies = await context.cookies()
      assert(cookies.filter(cookie => cookie.name.startsWith('cm_refresh')).every(cookie => cookie.httpOnly && cookie.sameSite === 'Lax'))
      assert(!(await page.evaluate(() => document.cookie)).includes('cm_refresh'))
      const headers = { Authorization: 'Token ' + accessToken }
      const list = await context.request.get(baseUrl + '/api/nafath-center/', { headers })
      assert.equal(list.status(), 200)
      const attachment = (await list.json()).data.find(item => item.hasFile && (account.role !== 'planning' || !item.isHidden))
      assert(attachment, account.role + ': no visible seeded attachment for download test')
      const scope = ['dean', 'finance', 'planning'].includes(account.role) ? account.role : 'agreement'
      const grant = await context.request.post(baseUrl + '/api/files/grants/', { headers, data: { kind: 'nafath-centers', agreementId: attachment.id, scope } })
      assert.equal(grant.status(), 200, account.role + ': grant failed')
      const ticket = (await grant.json()).data
      assert(!JSON.stringify(ticket).includes('/media/'))
      const downloaded = await context.request.get(ticket.downloadUrl, { headers: { ...headers, 'X-Download-Grant': ticket.grant } })
      assert.equal(downloaded.status(), 200)
      assert(downloaded.headers()['content-disposition'].includes('attachment;'))
      assert((await downloaded.body()).length > 0)
      assert.equal((await context.request.get(ticket.downloadUrl, { headers: { ...headers, 'X-Download-Grant': ticket.grant } })).status(), 409)
      assert.equal((await context.request.get(baseUrl + '/media/private/nonexistent.txt')).status(), 404)
      if (account.role === 'admin') {
        await page.goto(baseUrl + '/admin/security')
        await page.getByRole('heading', { name: 'الأمان والجلسات', exact: true }).waitFor()
        assert.equal(await page.getByLabel('مدة صلاحية إذن التنزيل بالثواني').inputValue(), '60')
        await page.goto(baseUrl + '/admin/roles')
        await page.getByLabel('الدور المراد إدارته').selectOption('contract')
        assert.equal(await page.locator('.permission-options label').filter({ hasText: 'تنزيل الملفات المرفقة' }).count(), 9)
      } else {
        assert.equal((await context.request.get(baseUrl + '/api/security-settings/', { headers })).status(), 403)
      }
      if (viewport.width < 768) await page.getByRole('button', { name: 'فتح القائمة', exact: true }).click()
      await page.locator('.logout').click()
      await page.waitForURL('**/login')
      await page.goto(baseUrl + '/home')
      await page.waitForURL('**/login')
      assert.equal((await context.request.get(baseUrl + '/api/auth/me/', { headers })).status(), 401)
      assert.deepEqual(errors, [], account.role + ': browser errors')
      console.log('PASS: ' + account.role + ' login, charts, navigation, cookie renewal, private storage, single-use download and logout at ' + viewport.width + 'px')
      await context.close()
    }
  }
} finally {
  await browser.close()
}
