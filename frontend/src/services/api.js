import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.1.143:8000/api/v1'

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

export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  logout: () => {
    localStorage.removeItem('authToken')
  },
  getProfile: () =>
    api.get('/auth/profile'),
}

export const dashboardAPI = {
  getSummary: () =>
    api.get('/dashboard/summary'),
  getTransactions: (limit = 10) =>
    api.get(`/transactions?limit=${limit}`),
}

export default api
