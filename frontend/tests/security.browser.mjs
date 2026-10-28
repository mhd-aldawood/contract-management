// Live local-Docker security workflow. Creates and removes only its own temporary account.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { createHash, randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const base = process.env.DASHBOARD_TEST_URL || 'http://cm.localhost:81'
assert(['localhost', '127.0.0.1', 'cm.localhost'].includes(new URL(base).hostname), 'This test is local-Docker only.')
const accounts = JSON.parse(await fs.readFile(process.env.DASHBOARD_TEST_ACCOUNTS, 'utf8'))
const admin = accounts.find(account => account.role === 'admin')
const username = 'cm_regression_security_' + randomUUID().replaceAll('-', '')
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH })
const context = await browser.newContext()
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(error.message))
page.setDefaultTimeout(15000)
let created = false
function database(code, envKey, value) {
  execFileSync('docker', ['compose', 'exec', '-T', '-e', `${envKey}=${value}`, 'backend', 'python', 'manage.py', 'shell', '-c', code], { cwd: process.cwd(), stdio: 'pipe' })
}
try {
  const adminLogin = await context.request.post(base + '/api/auth/login/', { data: { username: admin.username, password: admin.password } })
  assert.equal(adminLogin.status(), 200)
  const headers = { Authorization: 'Token ' + (await adminLogin.json()).data.token }
  const createdUser = await context.request.post(base + '/api/auth/users/', { headers, data: { username, roleCode: 'contract' } })
  assert.equal(createdUser.status(), 201)
  created = true
  const { temporaryPassword, user } = (await createdUser.json()).data
  await page.goto(base + '/login')
  await page.getByLabel('اسم المستخدم').fill(username)
  await page.getByLabel('كلمة المرور', { exact: true }).fill('Wrong-password-123!')
  await page.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click()
  await page.getByRole('alert').waitFor()
  assert(page.url().endsWith('/login'))
  await page.getByLabel('كلمة المرور', { exact: true }).fill(temporaryPassword)
  await page.getByRole('button', { name: 'تسجيل الدخول', exact: true }).click()
  await page.waitForURL('**/change-password')
  const replacement = 'Browser-Regression-Replace-561!'
  await page.getByLabel('كلمة المرور الحالية', { exact: true }).fill(temporaryPassword)
  await page.getByLabel('كلمة المرور الجديدة', { exact: true }).fill(replacement)
  await page.getByLabel('تأكيد كلمة المرور الجديدة', { exact: true }).fill(replacement + 'wrong')
  await page.getByRole('button', { name: 'تغيير كلمة المرور', exact: true }).click()
  await page.getByRole('alert').waitFor()
  await page.getByLabel('تأكيد كلمة المرور الجديدة', { exact: true }).fill(replacement)
  const changedPromise = page.waitForResponse(response => response.url().includes('/api/auth/change-password/'))
  await page.getByRole('button', { name: 'تغيير كلمة المرور', exact: true }).click()
  const changed = await changedPromise
  assert.equal(changed.status(), 200)
  let token = (await changed.json()).data.token
  await page.locator('.dashboard-stats').waitFor()
  const tokenHash = createHash('sha256').update(token).digest('hex')
  database("import os; from django.utils import timezone; from datetime import timedelta; from contract.security_models import AuthSession; assert AuthSession.objects.filter(access_hash=os.environ['CM_TEST_HASH']).update(access_expires_at=timezone.now()-timedelta(seconds=1)) == 1", 'CM_TEST_HASH', tokenHash)
  const renewalPromise = page.waitForResponse(response => response.url().includes('/api/auth/token/refresh/'))
  await page.getByRole('button', { name: 'تحديث البيانات', exact: true }).click()
  const renewed = await renewalPromise
  assert.equal(renewed.status(), 200)
  token = (await renewed.json()).data.token
  await page.getByRole('button', { name: 'تحديث البيانات', exact: true }).waitFor()
  assert(page.url().endsWith('/home'))
  assert.equal(await page.getByRole('alert').count(), 0)
  assert.equal((await context.request.get(base + '/api/security-settings/', { headers: { Authorization: 'Token ' + token } })).status(), 403)
  await page.goto(base + '/admin/security')
  await page.waitForURL('**/forbidden')
  const deactivated = await context.request.patch(base + `/api/auth/users/${user.id}/`, { headers, data: { isActive: false } })
  assert.equal(deactivated.status(), 200)
  await page.goto(base + '/home')
  await page.waitForURL('**/login')
  assert.deepEqual(errors, [])
  console.log('PASS: invalid login, first-login password change, mismatch validation, access expiry recovery, forbidden Admin page and deactivated-session redirect')
} finally {
  await browser.close()
  if (created) database("import os; from django.contrib.auth import get_user_model; name=os.environ['CM_TEST_USERNAME']; assert name.startswith('cm_regression_security_'); get_user_model().objects.filter(username=name).delete()", 'CM_TEST_USERNAME', username)
}
