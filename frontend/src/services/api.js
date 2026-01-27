/**
 * API Service
 *
 * Centralized API client for all backend communication.
 * Uses axios for HTTP requests with JWT authentication.
 *
 * @author Claude Code
 * @created January 24, 2026
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token and org_id to requests if they exist
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // Add org_id to data requests automatically
  const dataEndpoints = ['/clients', '/transactions', '/accounts', '/dashboard']
  const isDataRequest = dataEndpoints.some((endpoint) => config.url?.startsWith(endpoint))

  if (isDataRequest) {
    try {
      const userData = localStorage.getItem('authUser')
      if (userData) {
        const user = JSON.parse(userData)
        if (user.organization_id) {
          // Add to query params for GET requests
          if (config.method === 'get') {
            config.params = config.params || {}
            config.params.org_id = user.organization_id
          }
          // Add to body for POST/PUT requests (if body exists)
          if ((config.method === 'post' || config.method === 'put') && config.data) {
            const data = typeof config.data === 'string' ? JSON.parse(config.data) : config.data
            data.organization_id = user.organization_id
            config.data = data
          }
        }
      }
    } catch {
      // Ignore parse errors
    }
  }

  return config
})

// Handle response errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============================================================================
// AUTH API
// ============================================================================

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, password, name) => api.post('/auth/register', { email, password, name }),
  logout: () => localStorage.removeItem('authToken'),
  getProfile: () => api.get('/auth/profile'),
}

// ============================================================================
// USERS API (User Management)
// ============================================================================

export const usersAPI = {
  list: () => api.get('/auth/users'),
  getRoles: () => api.get('/auth/roles'),
  invite: (data) => api.post('/auth/users', data),
  updateRole: (userId, role) => api.put(`/auth/users/${userId}`, { role }),
  remove: (userId) => api.delete(`/auth/users/${userId}`),
}

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
}

// ============================================================================
// ORGANIZATIONS API
// ============================================================================

export const organizationsAPI = {
  list: (params = {}) => api.get('/organizations', { params }),
  get: (id) => api.get(`/organizations/${id}`),
}

// ============================================================================
// CLIENTS API
// ============================================================================

export const clientsAPI = {
  list: (params = {}) => api.get('/clients', { params }),
  get: (id) => api.get(`/clients/${id}`),
  create: (data) => api.post('/clients', data),
  update: (id, data) => api.put(`/clients/${id}`, data),
  delete: (id) => api.delete(`/clients/${id}`),
  getAccounts: (clientId, params = {}) => api.get(`/clients/${clientId}/accounts`, { params }),
}

// ============================================================================
// TRANSACTIONS API
// ============================================================================

export const transactionsAPI = {
  list: (params = {}) => api.get('/transactions', { params }),
  get: (id) => api.get(`/transactions/${id}`),
  create: (data) => api.post('/transactions', data),
  update: (id, data) => api.put(`/transactions/${id}`, data),
  delete: (id) => api.delete(`/transactions/${id}`),
  bulkDelete: (ids) => api.post('/transactions/bulk-delete', { ids }),
  bulkUpdateStatus: (ids, status) => api.put('/transactions/bulk-status', { ids, status }),
}

// ============================================================================
// ACCOUNTS API
// ============================================================================

export const accountsAPI = {
  list: (params = {}) => api.get('/accounts', { params }),
  get: (id) => api.get(`/accounts/${id}`),
}

// ============================================================================
// DATA QUALITY API
// ============================================================================

// Data quality routes use /api/data-quality prefix (not /api/v1)
const dqBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '/api/data-quality')
const dqApi = axios.create({
  baseURL: dqBase,
  headers: { 'Content-Type': 'application/json' },
})
dqApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
dqApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const dataQualityAPI = {
  getCoverage: (orgId) => dqApi.get(`/orgs/${orgId}/coverage`),
  getQuarantine: (orgId, resolved = false) => dqApi.get(`/orgs/${orgId}/quarantine`, { params: { resolved } }),
  resolveQuarantine: (orgId, quarantineId) => dqApi.post(`/orgs/${orgId}/quarantine/${quarantineId}/resolve`),
  resolveAllQuarantine: (orgId) => dqApi.post(`/orgs/${orgId}/quarantine/resolve-all`),
  getUnmappedTypes: (orgId) => dqApi.get(`/orgs/${orgId}/unmapped-types`),
  listMappings: (params = {}) => dqApi.get('/mappings', { params }),
  createMapping: (data) => dqApi.post('/mappings', null, { params: data }),
  updateMapping: (id, data) => dqApi.put(`/mappings/${id}`, null, { params: data }),
  deleteMapping: (id) => dqApi.delete(`/mappings/${id}`),
  rebuildFacts: (orgId) => dqApi.post(`/orgs/${orgId}/rebuild-facts`),
}

export default api
