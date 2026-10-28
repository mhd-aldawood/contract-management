import { getAccessToken } from '@/core/api/authSession'
// src/data/datasources/AuthRemoteDataSource.js
import { acceptSession } from "@/core/api/authSession";
import { API_URLS } from '@/core/config'
import { apiRequest } from '@/core/api/apiClient'

export default class AuthRemoteDataSource {
  async login({ username, password, rememberMe = false }) {
    const response = await apiRequest(API_URLS.auth.login, {
      method: "POST",
      body: JSON.stringify({ username, password, rememberMe }),
    });
    acceptSession(response.data);
    return response.data;
  }

  async logout() { await apiRequest(API_URLS.auth.logout, { method: 'POST', body: '{}' }); }

  async getAccessControl() {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.accessControl, {
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async me() {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.me, {
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async updateAccessControl(payload) {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async createRole(payload) {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async deleteRole(roleCode) {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.accessControl, {
      method: 'DELETE',
      body: JSON.stringify({ roleCode }),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async changePassword(payload) {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.changePassword, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    acceptSession(response.data);
    return response.data;
  }

  async getUsers(filters = {}) {
    const token = getAccessToken();
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
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.users, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }

  async updateUser(id, payload) {
    const token = getAccessToken();
    const response = await apiRequest(API_URLS.auth.userById(id), {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: token ? { Authorization: `Token ${token}` } : {},
    });
    return response.data;
  }
}
