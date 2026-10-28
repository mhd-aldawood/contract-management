// src/core/config/apiUrls.js

const configuredApiUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
const localHost = host => host === 'localhost' || host === '127.0.0.1' || host.endsWith('.localhost')
const useLocalGateway = typeof window !== 'undefined' && localHost(window.location.hostname) &&
  (!configuredApiUrl || localHost(new URL(configuredApiUrl, window.location.origin).hostname))
const API_BASE_URL = useLocalGateway ? '' : configuredApiUrl;

export const API_URLS = {
  contractRequests: { list: `${API_BASE_URL}/api/contract-requests/`, byId: id => `${API_BASE_URL}/api/contract-requests/${id}/` },
  doctoralContracts: { list: `${API_BASE_URL}/api/doctoral-contracts/`, byId: id => `${API_BASE_URL}/api/doctoral-contracts/${id}/` },
  base: API_BASE_URL,
  dashboard: `${API_BASE_URL}/api/dashboard/`,
  securitySettings: `${API_BASE_URL}/api/security-settings/`,
  fileGrant: `${API_BASE_URL}/api/files/grants/`,
  agreementOrders: {
    list: (kind, id, scope = 'agreement') => `${API_BASE_URL}/api/agreement-orders/${encodeURIComponent(kind)}/${id}/?scope=${encodeURIComponent(scope)}`,
    download: (kind, id, orderId, scope = 'agreement') => `${API_BASE_URL}/api/agreement-orders/${encodeURIComponent(kind)}/${id}/${orderId}/file/?scope=${encodeURIComponent(scope)}`,
  },

  auth: {
    csrf: `${API_BASE_URL}/api/auth/csrf/`,
    refresh: `${API_BASE_URL}/api/auth/token/refresh/`,
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
