// src/core/config/apiUrls.js

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

export const API_URLS = {
  base: API_BASE_URL,

  auth: {
    login: `${API_BASE_URL}/api/auth/login/`,
    logout: `${API_BASE_URL}/api/auth/logout/`,
    me: `${API_BASE_URL}/api/auth/me/`,
    accessControl: `${API_BASE_URL}/api/auth/access-control/`,
    changePassword: `${API_BASE_URL}/api/auth/change-password/`,
    users: `${API_BASE_URL}/api/auth/users/`,
    userById: (id) => `${API_BASE_URL}/api/auth/users/${id}/`,
  },

  agreements: {
    list: `${API_BASE_URL}/api/agreements`,
    create: `${API_BASE_URL}/api/agreements`,
    byId: (id) => `${API_BASE_URL}/api/agreements/${id}`,
    export: `${API_BASE_URL}/api/agreements/export`,
    filter: `${API_BASE_URL}/api/agreements/filter`,
    costs: `${API_BASE_URL}/api/agreements/costs`,
  },
  planning: {
    list: `${API_BASE_URL}/api/planning/agreements/`,
  },
  finance: {
    agreements: `${API_BASE_URL}/api/finance/agreements/`,
    orders: (kind, id) => `${API_BASE_URL}/api/finance/agreements/${encodeURIComponent(kind)}/${id}/orders/`,
    order: (kind, id, orderId) => `${API_BASE_URL}/api/finance/agreements/${encodeURIComponent(kind)}/${id}/orders/${orderId}/`,
    download: (kind, id, orderId) => `${API_BASE_URL}/api/finance/agreements/${encodeURIComponent(kind)}/${id}/orders/${orderId}/file/`,
  },
  dean: {
    agreements: `${API_BASE_URL}/api/dean/agreements/`,
    agreement: (kind, id) => `${API_BASE_URL}/api/dean/agreements/${encodeURIComponent(kind)}/${id}/`,
    visibility: (kind, id) => `${API_BASE_URL}/api/dean/agreements/${encodeURIComponent(kind)}/${id}/visibility/`,
    download: (kind, id, orderId) => `${API_BASE_URL}/api/dean/agreements/${encodeURIComponent(kind)}/${id}/orders/${orderId}/file/`,
  },

  educationalContents: {
    list: `${API_BASE_URL}/api/educational-contents`,
    create: `${API_BASE_URL}/api/educational-contents`,
    byId: (id) => `${API_BASE_URL}/api/educational-contents/${id}/`,
    save: `${API_BASE_URL}/api/educational-contents/save`,
  },
  nafathCenter: {
    list: `${API_BASE_URL}/api/nafath-center/`,
    create: `${API_BASE_URL}/api/nafath-center/create`,
  },
  lifeLong: {
    list: `${API_BASE_URL}/api/life-long/`,
    create: `${API_BASE_URL}/api/life-long/create`,
  },

  users: {
    profile: `${API_BASE_URL}/api/users/profile`,
    settings: `${API_BASE_URL}/api/users/settings`,
  },
    otherAgreement: {
    list: `${API_BASE_URL}/api/other-agreement/`,
    create: `${API_BASE_URL}/api/other-agreement/create`,
  },
  memorandum: {
    list: `${API_BASE_URL}/api/memorandum/`,
    create: `${API_BASE_URL}/api/memorandum/create`,
  },
};

export default API_URLS;
