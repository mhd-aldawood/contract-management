// src/data/repositories/AuthRepositoryImpl.js
import AuthRepository from "@/domain/repositories/AuthRepository";
import User from "@/domain/entities/User";
import { getAccessToken, refreshSession, clearSession } from '@/core/api/authSession'

export default class AuthRepositoryImpl extends AuthRepository {
  constructor({ localDataSource, remoteDataSource }) {
    super();
    this.local = localDataSource;
    this.remote = remoteDataSource;
    this.sessionVerified = false;
  }

  async login({ username, password, rememberMe = false }) {
    const data = await this.remote.login({ username, password, rememberMe });
    if (data.token) this.local.saveToken(data.token);
    const user = new User(data.user ?? { username });

    // ✅ استخدم saveSession الموجود
    this.local.saveSession(user);
    this.sessionVerified = true;

    return user;
  }

  getCurrentUser() {
    const session = this.local.getSession();
    if (!session) return null;
    return new User(session);
  }
  isAdmin() {
    return Boolean(this.getCurrentUser()?.isAdmin)
  }
  hasPermission(feature, action = 'read') {
    const user = this.getCurrentUser()
    if (!user) return false
    if (user.isAdmin) return true
    return Boolean(user.permissions?.[feature]?.[action])
  }
  async getAccessControl() {
    return this.remote.getAccessControl()
  }
  async updateAccessControl(payload) {
    return this.remote.updateAccessControl(payload)
  }
  async createRole(payload) {
    return this.remote.createRole(payload)
  }
  async deleteRole(roleCode) {
    return this.remote.deleteRole(roleCode)
  }
  async changePassword(payload) {
    const data = await this.remote.changePassword(payload)
    const user = new User(data)
    this.local.saveSession(user)
    this.sessionVerified = true
    return user
  }
  async getUsers(filters) {
    return this.remote.getUsers(filters)
  }
  async createUser(payload) {
    return this.remote.createUser(payload)
  }
  async updateUser(id, payload) {
    return this.remote.updateUser(id, payload)
  }
  async ensureCurrentUser() {
    if (!getAccessToken()) {
      const restored = await refreshSession()
      if (!restored) return null
    }

    const data = await this.remote.me()
    const user = new User(data)
    this.local.saveSession(user)
    this.sessionVerified = true
    return user
  }
  async logout(){
    try { await this.remote.logout() }
    finally { clearSession(); this.sessionVerified = false }
  }
}
