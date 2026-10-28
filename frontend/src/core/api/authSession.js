import { shallowRef } from 'vue'
import { API_URLS } from '@/core/config/apiUrls'

const currentUser = shallowRef(null)
let accessToken = ''
let csrfToken = ''
let refreshPromise = null

// Remove credentials and obsolete password-based browser authentication data.
for (const storage of [globalThis.localStorage, globalThis.sessionStorage]) {
  for (const key of ['access_token', 'refresh_token', 'app_session', 'app_users', 'app_educational_contents']) storage?.removeItem(key)
}
export const getAccessToken = () => accessToken
export const setAccessToken = token => { accessToken = token || '' }
export const getSessionUser = () => currentUser.value
export const setSessionUser = user => { currentUser.value = user }
export const clearSession = () => { accessToken = ''; csrfToken = ''; currentUser.value = null }
export function acceptSession(data) {
  accessToken = data.token || ''
  csrfToken = data.csrfToken || ''
  if (data.user) currentUser.value = data.user
}

export async function refreshSession() {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    try {
      {
        const csrf = await fetch(API_URLS.auth.csrf, { credentials: 'include', cache: 'no-store' })
        if (!csrf.ok) { clearSession(); return null }
        csrfToken = (await csrf.json()).data.csrfToken
      }
      const response = await fetch(API_URLS.auth.refresh, {
        method: 'POST', credentials: 'include', cache: 'no-store',
        headers: { 'X-Refresh-CSRF': csrfToken, 'Content-Type': 'application/json' }, body: '{}',
      })
      if (!response.ok) { clearSession(); return null }
      const result = await response.json()
      acceptSession(result.data)
      return currentUser.value
    } catch { clearSession(); return null }
    finally { refreshPromise = null }
  })()
  return refreshPromise
}

export async function authenticatedFetch(url, options = {}) {
  const publicAuth = /\/auth\/(login|csrf|token\/refresh)\//.test(url)
  let sentToken
  const send = () => {
    sentToken = accessToken
    const headers = new Headers(options.headers || {})
    headers.delete('Authorization')
    if (accessToken && !publicAuth) headers.set('Authorization', `Token ${accessToken}`)
    return fetch(url, { ...options, headers, credentials: 'include', cache: 'no-store' })
  }
  let response = await send()
  if (response.status === 401 && !publicAuth && !options.signal?.aborted) {
    if (sentToken && accessToken && accessToken !== sentToken) response = await send()
    else {
      const user = await refreshSession()
      if (user) response = await send()
      else globalThis.window?.dispatchEvent(new Event('auth:expired'))
    }
  }
  return response
}
