import { useEffect, useState } from 'react'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

export default function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    checkAuth()
    setReady(true)
  }, [checkAuth])

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    )
  }

  return isAuthenticated ? <Dashboard /> : <Login />
}
