/**
 * Home Page - Client Tiles Grid
 *
 * Main landing page showing all clients as clickable tiles.
 * 3 tiles per row, with basic info and pending actions placeholder.
 *
 * @author Claude Code
 * @created January 24, 2026
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { clientsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'
import Navigation from '../components/Navigation'
import { SkeletonGrid } from '../components/Skeleton'

export default function HomePage() {
  const navigate = useNavigate()
  const { addToast } = useToastStore()
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchClients()
  }, [])

  const fetchClients = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await clientsAPI.list({ limit: 100 })
      setClients(response.data.clients || [])
    } catch (err) {
      console.error('Error fetching clients:', err)
      setError(err.response?.data?.detail || 'Failed to load clients')
      addToast('Failed to load clients', 'error')
    } finally {
      setLoading(false)
    }
  }

  const filteredClients = clients.filter((client) =>
    client.name.toLowerCase().includes(search.toLowerCase()) ||
    (client.city && client.city.toLowerCase().includes(search.toLowerCase())) ||
    (client.industry && client.industry.toLowerCase().includes(search.toLowerCase()))
  )

  const handleClientClick = (clientId) => {
    navigate(`/client/${clientId}`)
  }

  // Mock pending actions for now - will be populated by AI later
  const getPendingActions = (clientId) => {
    // Placeholder: Random pending actions for demo
    const actions = [
      { type: 'invoice', count: Math.floor(Math.random() * 5), label: 'invoices to review' },
      { type: 'email', count: Math.floor(Math.random() * 3), label: 'emails pending' },
      { type: 'task', count: Math.floor(Math.random() * 4), label: 'tasks due' },
    ].filter(a => a.count > 0)
    return actions
  }

  if (error && clients.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md text-center">
            <div className="text-red-600 text-5xl mb-4">!</div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Unable to Load Clients
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
            <button
              onClick={fetchClients}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading && clients.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Clients</h1>
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
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Clients</h1>
              <p className="text-gray-600 dark:text-gray-400">
                {clients.length} client{clients.length !== 1 ? 's' : ''} in your practice
              </p>
            </div>
            {/* Search */}
            <div className="w-full md:w-80">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search clients..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Client Tiles Grid */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {filteredClients.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            {search ? 'No clients match your search' : 'No clients found'}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClients.map((client) => {
              const pendingActions = getPendingActions(client.id)
              const hasPendingActions = pendingActions.length > 0

              return (
                <div
                  key={client.id}
                  onClick={() => handleClientClick(client.id)}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-all cursor-pointer border-l-4 border-blue-500 hover:border-blue-600"
                >
                  {/* Client Header */}
                  <div className="p-4 border-b border-gray-100 dark:border-gray-700">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                          {client.name}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {client.industry || 'General Business'}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          client.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {client.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>

                  {/* Client Quick Info */}
                  <div className="p-4 space-y-2 text-sm">
                    <div className="flex items-center text-gray-600 dark:text-gray-400">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {client.city || 'No location'}{client.country ? `, ${client.country}` : ''}
                    </div>
                    {client.email && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400 truncate">
                        <svg className="w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span className="truncate">{client.email}</span>
                      </div>
                    )}
                    {client.tax_number && (
                      <div className="flex items-center text-gray-600 dark:text-gray-400">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        VAT: {client.tax_number}
                      </div>
                    )}
                  </div>

                  {/* Pending Actions (AI Placeholder) */}
                  <div className="px-4 pb-4">
                    {hasPendingActions ? (
                      <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
                        <div className="flex items-center mb-2">
                          <svg className="w-4 h-4 text-amber-600 dark:text-amber-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          <span className="text-xs font-medium text-amber-800 dark:text-amber-300">
                            Pending Actions
                          </span>
                        </div>
                        <div className="space-y-1">
                          {pendingActions.map((action, idx) => (
                            <div key={idx} className="text-xs text-amber-700 dark:text-amber-400">
                              {action.count} {action.label}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                        <div className="flex items-center">
                          <svg className="w-4 h-4 text-green-600 dark:text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <span className="text-xs font-medium text-green-800 dark:text-green-300">
                            All caught up
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
