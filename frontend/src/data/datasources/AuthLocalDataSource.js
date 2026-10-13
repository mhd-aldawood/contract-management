/**
 * Local storage backed data source.
 * Swap with an HTTP data source for a real backend.
 */
const USERS_KEY = 'app_users'
const SESSION_KEY = 'app_session'
const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
export default class AuthLocalDataSource {
  _getUsers() {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '[]')
  }

  _saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
  }

  async register(user) {
    const users = this._getUsers()
    if (users.find((u) => u.username === user.username)) {
      throw new Error('Username already exists')
    }
    users.push(user)
    this._saveUsers(users)
    return user
  }

  async findUser(username, password) {
    const users = this._getUsers()
    const user = users.find(
      (u) => u.username === username && u.password === password
    )
    if (!user) throw new Error('Invalid credentials')
    return user
  }

  saveSession(user) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user))
  }

  clearSession() {
    localStorage.removeItem(SESSION_KEY)
  }

  getSession() {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null')
  }
  saveToken(token) { localStorage.setItem(ACCESS_KEY, token) }
  getToken() { return localStorage.getItem(ACCESS_KEY) }
  saveRefreshToken(token) { localStorage.setItem(REFRESH_KEY, token) }
  getRefreshToken() { return localStorage.getItem(REFRESH_KEY) }
  clearTokens() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USERS_KEY)
  }
}