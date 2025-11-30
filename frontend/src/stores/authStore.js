import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  isAuthenticated: !!localStorage.getItem('authToken'),
  user: null,
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) throw new Error('Login failed')

      const data = await response.json()
      localStorage.setItem('authToken', data.token)
      set({ isAuthenticated: true, user: data.user, loading: false })
      return true
    } catch (error) {
      set({ error: error.message, loading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('authToken')
    set({ isAuthenticated: false, user: null })
  },

  checkAuth: () => {
    const token = localStorage.getItem('authToken')
    set({ isAuthenticated: !!token })
  },
}))
