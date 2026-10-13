// src/core/config/apiUrls.js

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export const API_URLS = {
  base: API_BASE_URL,

  auth: {
    login: `${API_BASE_URL}/api/auth/login/`,
    signup: `${API_BASE_URL}/api/auth/signup/`,
    logout: `${API_BASE_URL}/api/auth/logout/`,
    me: `${API_BASE_URL}/api/auth/me/`,
  },

  agreements: {
    list: `${API_BASE_URL}/api/agreements`,
    create: `${API_BASE_URL}/api/agreements`,
    byId: (id) => `${API_BASE_URL}/api/agreements/${id}`,
    export: `${API_BASE_URL}/api/agreements/export`,
    filter: `${API_BASE_URL}/api/agreements/filter`,
    costs: `${API_BASE_URL}/api/agreements/costs`,
  },

  educationalContents: {
    list: `${API_BASE_URL}/api/educational-contents`,
    create: `${API_BASE_URL}/api/educational-contents`,
    byId: (id) => `${API_BASE_URL}/api/educational-contents/${id}/`,
    save: `${API_BASE_URL}/api/educational-contents/save`,
  },
  nafathCenter: {
    create: `${API_BASE_URL}/api/nafath-center/create`,
  },
  lifeLong: {
    create: `${API_BASE_URL}/api/life-long/create`,
  },

  users: {
    profile: `${API_BASE_URL}/api/users/profile`,
    settings: `${API_BASE_URL}/api/users/settings`,
  },
    otherAgreement: {
    create: `${API_BASE_URL}/api/other-agreement/create`,
  },
};

export default API_URLS;
