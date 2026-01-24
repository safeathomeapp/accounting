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

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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
  logout: () => localStorage.removeItem('authToken'),
  getProfile: () => api.get('/auth/profile'),
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
}

// ============================================================================
// TRANSACTIONS API
// ============================================================================

export const transactionsAPI = {
  list: (params = {}) => api.get('/transactions', { params }),
  get: (id) => api.get(`/transactions/${id}`),
}

// ============================================================================
// ACCOUNTS API
// ============================================================================

export const accountsAPI = {
  list: (params = {}) => api.get('/accounts', { params }),
  get: (id) => api.get(`/accounts/${id}`),
}

export default api
