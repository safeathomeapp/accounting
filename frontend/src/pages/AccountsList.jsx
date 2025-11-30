import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useToastStore } from '../stores/toastStore'
import Navigation from '../components/Navigation'
import { SkeletonGrid } from '../components/Skeleton'

export default function AccountsList() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [platformFilter, setPlatformFilter] = useState('')

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('authToken')
      const response = await fetch('http://localhost:8000/api/v1/sync/status', {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        // Use mock data for demo
        setAccounts(generateMockAccounts())
      } else {
        const data = await response.json()
        setAccounts(data.accounts || generateMockAccounts())
      }
      setError(null)
    } catch (err) {
      console.error('Error fetching accounts:', err)
      // Use mock data on error
      setAccounts(generateMockAccounts())
    } finally {
      setLoading(false)
    }
  }

  const generateMockAccounts = () => [
    {
      id: '1',
      name: 'Business Bank Account',
      platform: 'Xero',
      code: 'BANK-001',
      type: 'Bank',
      balance: 25430.50,
      currency: 'GBP',
      active: true,
      lastSync: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '2',
      name: 'Savings Account',
      platform: 'Xero',
      code: 'SAV-001',
      type: 'Savings',
      balance: 10000.00,
      currency: 'GBP',
      active: true,
      lastSync: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '3',
      name: 'Client Receivables',
      platform: 'QuickBooks',
      code: 'AR-001',
      type: 'Receivable',
      balance: 5230.75,
      currency: 'GBP',
      active: true,
      lastSync: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '4',
      name: 'Tax Payable',
      platform: 'Xero',
      code: 'TAX-001',
      type: 'Payable',
      balance: -3500.00,
      currency: 'GBP',
      active: true,
      lastSync: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    },
  ]

  const filteredAccounts = accounts.filter((a) => {
    const matchesSearch = a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.code.toLowerCase().includes(search.toLowerCase())
    const matchesPlatform = !platformFilter || a.platform === platformFilter
    return matchesSearch && matchesPlatform
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSync = async (accountId) => {
    try {
      addToast('Starting sync...', 'info')
      const token = localStorage.getItem('authToken')
      const response = await fetch('http://localhost:8000/api/v1/sync/all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        addToast('Sync completed successfully!', 'success')
        await fetchAccounts()
      } else {
        addToast('Sync failed', 'error')
      }
    } catch (err) {
      addToast('Sync error: ' + err.message, 'error')
    }
  }

  if (loading && accounts.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <SkeletonGrid />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />

      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Accounts & Clients</h1>
            <p className="text-gray-600">View all connected accounts and client information</p>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search by name or code
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Platform Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Platform
              </label>
              <select
                value={platformFilter}
                onChange={(e) => setPlatformFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Platforms</option>
                <option value="Xero">Xero</option>
                <option value="QuickBooks">QuickBooks</option>
              </select>
            </div>
          </div>
        </div>

        {/* Accounts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredAccounts.length === 0 ? (
            <div className="col-span-2 text-center py-12 text-gray-500">
              No accounts found
            </div>
          ) : (
            filteredAccounts.map((account) => (
              <div
                key={account.id}
                className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{account.name}</h3>
                    <p className="text-sm text-gray-600">{account.code}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    account.platform === 'Xero'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {account.platform}
                  </span>
                </div>

                {/* Details */}
                <div className="space-y-3 mb-6 pb-6 border-b border-gray-200">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Type:</span>
                    <span className="text-gray-900 font-medium">{account.type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Currency:</span>
                    <span className="text-gray-900 font-medium">{account.currency}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Balance:</span>
                    <span className={`text-lg font-bold ${
                      account.balance >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {account.currency} {account.balance.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex justify-between items-center">
                  <div className="text-xs text-gray-500">
                    Last sync:{' '}
                    {new Date(account.lastSync).toLocaleString()}
                  </div>
                  <button
                    onClick={() => handleSync(account.id)}
                    className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 transition"
                  >
                    Sync Now
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Summary Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Total Accounts</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {filteredAccounts.length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Total Balance</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              £{filteredAccounts.reduce((sum, a) => sum + a.balance, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Active Accounts</p>
            <p className="text-3xl font-bold text-green-600 mt-1">
              {filteredAccounts.filter((a) => a.active).length}
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
