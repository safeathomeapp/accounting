import { Link, useLocation } from 'react-router-dom'
import DarkModeToggle from './DarkModeToggle'

export default function Navigation() {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="bg-gray-800 dark:bg-gray-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="font-bold text-white">A</span>
            </div>
            <span className="font-bold text-lg">Accountancy</span>
          </Link>

          {/* Menu & Toggle */}
          <div className="flex items-center space-x-1">
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
              to="/transactions"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/transactions')
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Transactions
            </Link>
            <Link
              to="/accounts"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/accounts')
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Accounts
            </Link>
            <Link
              to="/sync"
              className={`px-4 py-2 rounded-lg transition ${
                isActive('/sync')
                  ? 'bg-blue-600'
                  : 'hover:bg-gray-700'
              }`}
            >
              Sync Monitor
            </Link>
            <DarkModeToggle />
          </div>
        </div>
      </div>
    </nav>
  )
}
