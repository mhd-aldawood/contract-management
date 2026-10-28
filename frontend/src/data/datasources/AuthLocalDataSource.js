import { getSessionUser, setSessionUser, getAccessToken, setAccessToken, clearSession } from '@/core/api/authSession'

export default class AuthLocalDataSource {
  saveSession(user) { setSessionUser(user) }
  getSession() { return getSessionUser() }
  clearSession() { clearSession() }
  saveToken(token) { setAccessToken(token) }
  getToken() { return getAccessToken() }
  clearTokens() { clearSession() }
}
