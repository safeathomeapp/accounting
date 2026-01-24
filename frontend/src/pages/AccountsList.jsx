/**
 * Accounts List Page
 *
 * Displays chart of accounts from PostgreSQL database with filtering.
 *
 * @author Claude Code
 * @updated January 24, 2026
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useToastStore } from '../stores/toastStore'
import { accountsAPI, clientsAPI } from '../services/api'
import Navigation from '../components/Navigation'
import { SkeletonGrid } from '../components/Skeleton'

export default function AccountsList() {
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const [accounts, setAccounts] = useState([])
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [activeTab, setActiveTab] = useState('accounts')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [accountsRes, clientsRes] = await Promise.all([
        accountsAPI.list({ limit: 100 }),
        clientsAPI.list({ limit: 100 }),
      ])

      setAccounts(accountsRes.data.accounts || [])
      setClients(clientsRes.data.clients || [])
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err.response?.data?.detail || 'Failed to load data')
      addToast('Failed to load data', 'error')
    } finally {
      setLoading(false)
    }
  }

  const filteredAccounts = accounts.filter((a) => {
    const matchesSearch =
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.code.toLowerCase().includes(search.toLowerCase())
    const matchesType = !typeFilter || a.account_type === typeFilter
    return matchesSearch && matchesType
  })

  const filteredClients = clients.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.email && c.email.toLowerCase().includes(search.toLowerCase()))
    return matchesSearch
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Get unique account types for filter dropdown
  const accountTypes = [...new Set(accounts.map((a) => a.account_type).filter(Boolean))]

  if (error && accounts.length === 0 && clients.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md text-center">
            <div className="text-red-600 text-5xl mb-4">!</div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Unable to Load Data
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
            <button
              onClick={fetchData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading && accounts.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Accounts & Clients</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <SkeletonGrid />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Accounts & Clients</h1>
            <p className="text-gray-600 dark:text-gray-400">
              {accounts.length} accounts, {clients.length} clients
            </p>
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
        {/* Tab Navigation */}
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setActiveTab('accounts')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'accounts'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            Chart of Accounts ({accounts.length})
          </button>
          <button
            onClick={() => setActiveTab('clients')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              activeTab === 'clients'
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            Clients ({clients.length})
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={activeTab === 'accounts' ? 'Search by name or code...' : 'Search by name or email...'}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Type Filter (Accounts only) */}
            {activeTab === 'accounts' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Account Type
                </label>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">All Types</option>
                  {accountTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        {activeTab === 'accounts' ? (
          /* Accounts Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAccounts.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
                No accounts found
              </div>
            ) : (
              filteredAccounts.map((account) => (
                <div
                  key={account.id}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                        {account.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{account.code}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        account.account_type === 'Revenue'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                          : account.account_type === 'Expense'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                          : account.account_type === 'Asset'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                          : account.account_type === 'Liability'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {account.account_type}
                    </span>
                  </div>
                  {account.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {account.description}
                    </p>
                  )}
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                    <span
                      className={`w-2 h-2 rounded-full mr-2 ${
                        account.is_active ? 'bg-green-500' : 'bg-gray-400'
                      }`}
                    ></span>
                    {account.is_active ? 'Active' : 'Inactive'}
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          /* Clients Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredClients.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
                No clients found
              </div>
            ) : (
              filteredClients.map((client) => (
                <div
                  key={client.id}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                        {client.name}
                      </h3>
                      {client.industry && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">{client.industry}</p>
                      )}
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        client.contact_type === 'customer'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                          : client.contact_type === 'supplier'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {client.contact_type
                        ? client.contact_type.charAt(0).toUpperCase() + client.contact_type.slice(1)
                        : 'Client'}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm">
                    {client.email && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <span className="w-16 font-medium">Email:</span>
                        <span>{client.email}</span>
                      </div>
                    )}
                    {client.phone && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <span className="w-16 font-medium">Phone:</span>
                        <span>{client.phone}</span>
                      </div>
                    )}
                    {client.city && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <span className="w-16 font-medium">City:</span>
                        <span>
                          {client.city}
                          {client.country && `, ${client.country}`}
                        </span>
                      </div>
                    )}
                    {client.tax_number && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <span className="w-16 font-medium">VAT:</span>
                        <span>{client.tax_number}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Summary Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Total Accounts</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{accounts.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Total Clients</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{clients.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Active Items</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">
              {accounts.filter((a) => a.is_active).length + clients.filter((c) => c.is_active).length}
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
