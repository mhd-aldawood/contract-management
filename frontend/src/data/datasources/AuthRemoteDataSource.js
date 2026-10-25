// src/data/datasources/AuthRemoteDataSource.js
import { createLogger } from "@/core/logger";
import { API_URLS } from '@/core/config'
import { apiRequest } from '@/core/api/apiClient'

const log = createLogger("AuthRemoteDataSource");
export default class AuthRemoteDataSource {
  async login({ username, password }) {
    log.debug('login request', { username });
    const response = await apiRequest(API_URLS.auth.login, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    log.debug('login response', response);
    return response.data;
  }

  async getAccessControl() {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.accessControl, {
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async me() {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.me, {
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async updateAccessControl(payload) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async createRole(payload) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async deleteRole(roleCode) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'DELETE',
      body: JSON.stringify({ roleCode }),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async changePassword(payload) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.changePassword, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async getUsers(filters = {}) {
    const token = localStorage.getItem('access_token');
    const query = new URLSearchParams();
    if (filters.q) query.set('q', filters.q);
    if (filters.role) query.set('role', filters.role);
    if (filters.active !== '') query.set('active', filters.active);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    const response = await apiRequest(`${API_URLS.auth.users}${suffix}`, {
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async createUser(payload) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.users, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async updateUser(id, payload) {
    const token = localStorage.getItem('access_token');
    const response = await apiRequest(API_URLS.auth.userById(id), {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }
}
