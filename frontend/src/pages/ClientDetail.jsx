/**
 * Client Detail Page
 *
 * Individual client view with:
 * - Client details block
 * - Transactions/accounts block
 * - Pending actions block (AI placeholder)
 * - Important dates/messages block
 *
 * @author Claude Code
 * @created January 24, 2026
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { clientsAPI, transactionsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'
import Navigation from '../components/Navigation'
import { SkeletonCard } from '../components/Skeleton'

export default function ClientDetail() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const { addToast } = useToastStore()
  const [client, setClient] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchClientData()
  }, [clientId])

  const fetchClientData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch client details and their transactions in parallel
      const [clientRes, transactionsRes] = await Promise.all([
        clientsAPI.get(clientId),
        transactionsAPI.list({ client_id: clientId, limit: 100 }),
      ])

      setClient(clientRes.data)
      setTransactions(transactionsRes.data.transactions || [])
    } catch (err) {
      console.error('Error fetching client data:', err)
      setError(err.response?.data?.detail || 'Failed to load client')
      addToast('Failed to load client data', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Calculate summary stats
  const stats = {
    totalTransactions: transactions.length,
    totalInvoices: transactions.filter(t => t.transaction_type === 'invoice').length,
    totalBills: transactions.filter(t => t.transaction_type === 'bill').length,
    totalRevenue: transactions
      .filter(t => t.transaction_type === 'invoice')
      .reduce((sum, t) => sum + (t.total_amount || 0), 0),
    totalExpenses: transactions
      .filter(t => t.transaction_type === 'bill')
      .reduce((sum, t) => sum + (t.total_amount || 0), 0),
    overdueCount: transactions.filter(t => t.status === 'overdue').length,
    pendingCount: transactions.filter(t => ['draft', 'submitted'].includes(t.status)).length,
  }

  // Mock pending actions - will be populated by AI
  const pendingActions = [
    { id: 1, type: 'invoice', title: 'Review Q4 invoices', priority: 'high', dueDate: '2026-01-28' },
    { id: 2, type: 'email', title: 'Send payment reminder', priority: 'medium', dueDate: '2026-01-26' },
    { id: 3, type: 'reconcile', title: 'Reconcile bank statement', priority: 'low', dueDate: '2026-02-01' },
  ]

  // Mock important dates
  const importantDates = [
    { id: 1, type: 'vat', title: 'VAT Return Due', date: '2026-02-07', status: 'upcoming' },
    { id: 2, type: 'accounts', title: 'Year End', date: '2026-03-31', status: 'upcoming' },
    { id: 3, type: 'payment', title: 'Corporation Tax', date: '2026-01-01', status: 'overdue' },
  ]

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md text-center">
            <div className="text-red-600 text-5xl mb-4">!</div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Client Not Found
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
            <button
              onClick={() => navigate('/home')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Back to Clients
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />

      {/* Header with Back Button */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/home')}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            >
              <svg className="w-6 h-6 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{client?.name}</h1>
              <p className="text-gray-600 dark:text-gray-400">{client?.industry || 'Client'}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left Column - Client Details */}
          <div className="space-y-6">
            {/* Client Info Block */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Client Details
              </h2>
              <div className="space-y-3 text-sm">
                {client?.email && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-500 dark:text-gray-400">Email:</span>
                    <a href={`mailto:${client.email}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                      {client.email}
                    </a>
                  </div>
                )}
                {client?.phone && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-500 dark:text-gray-400">Phone:</span>
                    <span className="text-gray-900 dark:text-white">{client.phone}</span>
                  </div>
                )}
                {client?.website && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-500 dark:text-gray-400">Website:</span>
                    <a href={client.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                      {client.website}
                    </a>
                  </div>
                )}
                <div className="flex items-start">
                  <span className="w-20 text-gray-500 dark:text-gray-400">Address:</span>
                  <div className="text-gray-900 dark:text-white">
                    {client?.address_line1 && <div>{client.address_line1}</div>}
                    {client?.address_line2 && <div>{client.address_line2}</div>}
                    {client?.city && <div>{client.city}{client?.postal_code ? `, ${client.postal_code}` : ''}</div>}
                    {client?.country && <div>{client.country}</div>}
                  </div>
                </div>
                {client?.tax_number && (
                  <div className="flex items-start">
                    <span className="w-20 text-gray-500 dark:text-gray-400">VAT No:</span>
                    <span className="text-gray-900 dark:text-white">{client.tax_number}</span>
                  </div>
                )}
                <div className="flex items-start">
                  <span className="w-20 text-gray-500 dark:text-gray-400">Type:</span>
                  <span className="text-gray-900 dark:text-white capitalize">{client?.contact_type || 'Customer'}</span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Quick Stats
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.totalInvoices}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">Invoices</div>
                </div>
                <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    £{stats.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">Revenue</div>
                </div>
                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.overdueCount}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">Overdue</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.pendingCount}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">Pending</div>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column - Transactions */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 h-full">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Recent Transactions
                </h2>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {transactions.length} total
                </span>
              </div>

              {transactions.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No transactions found
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {transactions.slice(0, 10).map((txn) => (
                    <div
                      key={txn.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              txn.transaction_type === 'invoice'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                            }`}
                          >
                            {txn.transaction_type === 'invoice' ? 'INV' : 'BILL'}
                          </span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {txn.reference_number || txn.description}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {txn.transaction_date ? new Date(txn.transaction_date).toLocaleDateString() : 'No date'}
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          £{(txn.total_amount || 0).toFixed(2)}
                        </div>
                        <span
                          className={`text-xs ${
                            txn.status === 'paid' ? 'text-green-600 dark:text-green-400' :
                            txn.status === 'overdue' ? 'text-red-600 dark:text-red-400' :
                            'text-gray-500 dark:text-gray-400'
                          }`}
                        >
                          {txn.status}
                        </span>
                      </div>
                    </div>
                  ))}
                  {transactions.length > 10 && (
                    <button
                      onClick={() => navigate(`/transactions?client_id=${clientId}`)}
                      className="w-full py-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      View all {transactions.length} transactions
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Actions & Dates */}
          <div className="space-y-6">
            {/* Pending Actions Block (AI Placeholder) */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Pending Actions
                </h2>
              </div>
              <div className="space-y-3">
                {pendingActions.map((action) => (
                  <div
                    key={action.id}
                    className={`p-3 rounded-lg border-l-4 ${
                      action.priority === 'high'
                        ? 'bg-red-50 dark:bg-red-900/20 border-red-500'
                        : action.priority === 'medium'
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500'
                        : 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {action.title}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Due: {new Date(action.dueDate).toLocaleDateString()}
                        </div>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          action.priority === 'high'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                            : action.priority === 'medium'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                        }`}
                      >
                        {action.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                  AI-powered actions coming soon
                </p>
              </div>
            </div>

            {/* Important Dates Block */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Important Dates
                </h2>
              </div>
              <div className="space-y-3">
                {importantDates.map((item) => (
                  <div
                    key={item.id}
                    className={`p-3 rounded-lg flex items-center justify-between ${
                      item.status === 'overdue'
                        ? 'bg-red-50 dark:bg-red-900/20'
                        : 'bg-gray-50 dark:bg-gray-700/50'
                    }`}
                  >
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {item.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(item.date).toLocaleDateString()}
                      </div>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        item.status === 'overdue'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                          : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
