// src/data/datasources/AuthRemoteDataSource.js
import { createLogger } from "@/core/logger";
import { API_URLS } from '@/core/config'
import { apiRequest } from '@/core/api/apiClient'

const log = createLogger("AuthRemoteDataSource");
export default class AuthRemoteDataSource {
  async signup({ username, email, password, password2 }) {
    log.debug('signup request', { username, email });
    const response = await apiRequest(API_URLS.auth.signup, {
      method: "POST",
      body: JSON.stringify({ username, email, password, password2 }),
    });
    log.debug('signup response', response);
    return response.data;
  }

  async login({ username, password }) {
    log.debug('login request', { username });
    const response = await apiRequest(API_URLS.auth.login, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    log.debug('login response', response);
    return response.data;
  }
}
