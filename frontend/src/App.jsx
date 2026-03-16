import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useThemeStore } from './stores/themeStore'
import ErrorBoundary from './components/ErrorBoundary'
import Toast from './components/Toast'
import Login from './pages/Login'
import Register from './pages/Register'
import HomePage from './pages/HomePage'
import ClientDetail from './pages/ClientDetail'
import Dashboard from './pages/Dashboard'
import TransactionList from './pages/TransactionList'
import AccountsList from './pages/AccountsList'
import SyncMonitor from './pages/SyncMonitor'
import Settings from './pages/Settings'
import DataQuality from './pages/DataQuality'
import DocumentReview from './pages/DocumentReview'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()
  const { initTheme } = useThemeStore()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    initTheme()
    checkAuth()
    setReady(true)
  }, [checkAuth, initTheme])

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
        <div className="text-xl text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Toast />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/client/:clientId"
            element={
              <ProtectedRoute>
                <ClientDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/transactions"
            element={
              <ProtectedRoute>
                <TransactionList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/accounts"
            element={
              <ProtectedRoute>
                <AccountsList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sync"
            element={
              <ProtectedRoute>
                <SyncMonitor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/data-quality"
            element={
              <ProtectedRoute>
                <DataQuality />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents/review"
            element={
              <ProtectedRoute>
                <DocumentReview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/client/:clientId/documents/review"
            element={
              <ProtectedRoute>
                <DocumentReview />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to={isAuthenticated ? "/home" : "/login"} replace />} />
          <Route path="*" element={<Navigate to={isAuthenticated ? "/home" : "/login"} replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
