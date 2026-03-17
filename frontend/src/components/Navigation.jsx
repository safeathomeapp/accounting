import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import DarkModeToggle from './DarkModeToggle'

export default function Navigation() {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout, user } = useAuthStore()

  const isActive = (path) => location.pathname === path
  const isClientPage = location.pathname.startsWith('/client/')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="bg-gray-800 dark:bg-gray-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Company Name */}
          <div className="flex items-center space-x-3">
            <Link to="/home" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="font-bold text-white">{user?.name?.[0]?.toUpperCase() || 'A'}</span>
              </div>
              <span className="font-bold text-lg">{user?.name || 'Accountancy'}</span>
            </Link>
            {/* Settings Cog - for future user/company management */}
            <Link
              to="/settings"
              className="p-2 rounded-lg hover:bg-gray-700 transition"
              title="Settings"
            >
              <svg className="w-5 h-5 text-gray-400 hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </Link>
          </div>

          {/* Menu & Toggle */}
          <div className="flex items-center space-x-1">
            <Link
              to="/home"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/home') || isClientPage
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Clients
            </Link>
            <Link
              to="/dashboard"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/dashboard')
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/sync"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/sync')
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Sync
            </Link>
            <DarkModeToggle />

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="ml-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition text-sm font-medium"
              title={user?.email || 'Logout'}
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
