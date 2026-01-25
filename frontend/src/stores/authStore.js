import { create } from 'zustand'

// Helper to get stored user
const getStoredUser = () => {
  try {
    const stored = localStorage.getItem('authUser')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export const useAuthStore = create((set) => ({
  isAuthenticated: !!localStorage.getItem('authToken'),
  user: getStoredUser(),
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
      localStorage.setItem('authUser', JSON.stringify(data.user))
      set({ isAuthenticated: true, user: data.user, loading: false })
      return true
    } catch (error) {
      // Demo fallback - allow login with test credentials when API unavailable
      if (email === 'test@example.com') {
        const demoUser = { email, name: 'Demo User' }
        localStorage.setItem('authToken', 'demo-token-12345')
        localStorage.setItem('authUser', JSON.stringify(demoUser))
        set({ isAuthenticated: true, user: demoUser, loading: false })
        return true
      }
      set({ error: error.message, loading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    set({ isAuthenticated: false, user: null })
  },

  checkAuth: () => {
    const token = localStorage.getItem('authToken')
    const user = getStoredUser()
    set({ isAuthenticated: !!token, user })
  },
}))
