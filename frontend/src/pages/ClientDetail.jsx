/**
 * Client Detail Page - Central Hub
 *
 * Individual client view with:
 * - Client info header with quick actions
 * - Tabs: Transactions / Accounts / Documents
 * - Summary stats sidebar
 * - Pending actions (AI placeholder)
 *
 * @author Claude Code
 * @created January 24, 2026
 * @updated January 25, 2026
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { clientsAPI, transactionsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'
import Navigation from '../components/Navigation'
import { SkeletonCard } from '../components/Skeleton'
import { useSortedItems } from '../hooks/useSortedItems'
import ClientFormModal from '../components/ClientFormModal'
import TransactionFormModal from '../components/TransactionFormModal'
import ConfirmDialog from '../components/ConfirmDialog'

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

export default function ClientDetail() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const { addToast } = useToastStore()
  const [client, setClient] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('transactions')

  // Modal states
  const [showClientEdit, setShowClientEdit] = useState(false)
  const [showTxnForm, setShowTxnForm] = useState(false)
  const [editingTxn, setEditingTxn] = useState(null)
  const [txnFormDefaults, setTxnFormDefaults] = useState({})
  const [deleteTarget, setDeleteTarget] = useState(null) // { type: 'client' | 'transaction', id }
  const [deleteLoading, setDeleteLoading] = useState(false)

  // Transaction filters and pagination
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)

  useEffect(() => {
    fetchClientData()
  }, [clientId])

  const fetchClientData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch client details and transactions first
      const [clientRes, transactionsRes] = await Promise.all([
        clientsAPI.get(clientId),
        transactionsAPI.list({ client_id: clientId, limit: 100 }),
      ])

      setClient(clientRes.data)
      setTransactions(transactionsRes.data.transactions || [])

      // Fetch client-specific accounts
      const accountsRes = await clientsAPI.getAccounts(clientId)
      setAccounts(accountsRes.data.accounts || [])
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
    paidCount: transactions.filter(t => t.status === 'paid').length,
  }

  // Filter transactions
  const filteredTransactions = transactions.filter((t) => {
    const matchesSearch =
      !search ||
      (t.description && t.description.toLowerCase().includes(search.toLowerCase())) ||
      (t.reference_number && t.reference_number.toLowerCase().includes(search.toLowerCase()))
    const matchesType = !typeFilter || t.transaction_type === typeFilter
    const matchesStatus = !statusFilter || t.status === statusFilter
    return matchesSearch && matchesType && matchesStatus
  })

  // Sorting
  const sort = useSortedItems(filteredTransactions)
  const sortedTransactions = sort.getSorted()

  // Pagination
  const totalPages = Math.ceil(sortedTransactions.length / itemsPerPage)
  const paginatedTransactions = sortedTransactions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [search, typeFilter, statusFilter, itemsPerPage])

  // Get unique statuses for filter dropdown
  const uniqueStatuses = [...new Set(transactions.map(t => t.status).filter(Boolean))]

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

  const openNewTxn = (type) => {
    setEditingTxn(null)
    setTxnFormDefaults({ transaction_type: type })
    setShowTxnForm(true)
  }

  const openEditTxn = (txn) => {
    setEditingTxn(txn)
    setShowTxnForm(true)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    try {
      if (deleteTarget.type === 'client') {
        await clientsAPI.delete(deleteTarget.id)
        addToast('Client deactivated', 'success')
        navigate('/home')
      } else {
        await transactionsAPI.delete(deleteTarget.id)
        addToast('Transaction deleted', 'success')
        setDeleteTarget(null)
        fetchClientData()
      }
    } catch (err) {
      addToast(err.response?.data?.detail || 'Delete failed', 'error')
    } finally {
      setDeleteLoading(false)
    }
  }

  const tabs = [
    { id: 'transactions', label: 'Transactions', count: transactions.length },
    { id: 'accounts', label: 'Accounts', count: accounts.length },
    { id: 'documents', label: 'Documents', count: 0 },
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
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-3"><SkeletonCard /></div>
            <div><SkeletonCard /></div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />

      {/* Header with Client Info and Quick Actions */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Left: Back button and client name */}
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
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{client?.name}</h1>
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <span className="capitalize">{client?.contact_type || 'Customer'}</span>
                  {client?.industry && (
                    <>
                      <span>•</span>
                      <span>{client.industry}</span>
                    </>
                  )}
                  {client?.email && (
                    <>
                      <span>•</span>
                      <a href={`mailto:${client.email}`} className="text-blue-600 dark:text-blue-400 hover:underline">
                        {client.email}
                      </a>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => openNewTxn('invoice')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2 text-sm font-medium"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                New Invoice
              </button>
              <button
                onClick={() => openNewTxn('payment')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 text-sm font-medium"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z" />
                </svg>
                Record Payment
              </button>
              <button
                onClick={() => navigate(`/client/${clientId}/documents/review`)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center gap-2 text-sm font-medium"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v5a2 2 0 002 2h5" />
                </svg>
                AI OCR
              </button>
              <button
                onClick={() => setShowClientEdit(true)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
                title="Edit Client"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={() => setDeleteTarget({ type: 'client', id: clientId })}
                className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition"
                title="Delete Client"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content Area - 3 columns */}
          <div className="lg:col-span-3 space-y-6">
            {/* Summary Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  £{stats.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Invoiced</div>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.paidCount}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Paid</div>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.pendingCount}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Pending</div>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.overdueCount}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Overdue</div>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              {/* Tab Headers */}
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex -mb-px">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-6 py-4 text-sm font-medium border-b-2 transition ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                      }`}
                    >
                      {tab.label}
                      {tab.count > 0 && (
                        <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                          activeTab === tab.id
                            ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}>
                          {tab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {/* Transactions Tab */}
                {activeTab === 'transactions' && (
                  <div>
                    {transactions.length === 0 ? (
                      <div className="text-center py-12">
                        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">No transactions yet</p>
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm">
                          Create First Invoice
                        </button>
                      </div>
                    ) : (
                      <div>
                        {/* Filters Row */}
                        <div className="flex flex-wrap gap-4 mb-4">
                          {/* Search */}
                          <div className="flex-1 min-w-[200px]">
                            <input
                              type="text"
                              value={search}
                              onChange={(e) => setSearch(e.target.value)}
                              placeholder="Search description, reference..."
                              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                          </div>
                          {/* Type Filter */}
                          <select
                            value={typeFilter}
                            onChange={(e) => setTypeFilter(e.target.value)}
                            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">All Types</option>
                            <option value="invoice">Invoice</option>
                            <option value="bill">Bill</option>
                          </select>
                          {/* Status Filter */}
                          <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">All Statuses</option>
                            {uniqueStatuses.map((status) => (
                              <option key={status} value={status}>
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                              </option>
                            ))}
                          </select>
                          {/* Clear Filters */}
                          {(search || typeFilter || statusFilter) && (
                            <button
                              onClick={() => {
                                setSearch('')
                                setTypeFilter('')
                                setStatusFilter('')
                              }}
                              className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                            >
                              Clear
                            </button>
                          )}
                        </div>

                        {/* Results info */}
                        <div className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                          Showing {paginatedTransactions.length} of {filteredTransactions.length} transactions
                          {filteredTransactions.length !== transactions.length && ` (filtered from ${transactions.length})`}
                        </div>

                        {/* Table */}
                        {filteredTransactions.length === 0 ? (
                          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            No transactions match your filters
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full">
                              <thead>
                                <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                  <th
                                    className="pb-3 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('transaction_type')}
                                  >
                                    Type {sort.getSortIndicator('transaction_type')}
                                  </th>
                                  <th
                                    className="pb-3 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('reference_number')}
                                  >
                                    Reference {sort.getSortIndicator('reference_number')}
                                  </th>
                                  <th
                                    className="pb-3 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('transaction_date')}
                                  >
                                    Date {sort.getSortIndicator('transaction_date')}
                                  </th>
                                  <th
                                    className="pb-3 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('due_date')}
                                  >
                                    Due Date {sort.getSortIndicator('due_date')}
                                  </th>
                                  <th
                                    className="pb-3 text-right cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('total_amount')}
                                  >
                                    Amount {sort.getSortIndicator('total_amount')}
                                  </th>
                                  <th
                                    className="pb-3 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => sort.toggleSort('status')}
                                  >
                                    Status {sort.getSortIndicator('status')}
                                  </th>
                                  <th className="pb-3 text-right">Actions</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                                {paginatedTransactions.map((txn) => (
                                  <tr key={txn.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <td className="py-3">
                                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        txn.transaction_type === 'invoice'
                                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                                      }`}>
                                        {txn.transaction_type === 'invoice' ? 'Invoice' : 'Bill'}
                                      </span>
                                    </td>
                                    <td className="py-3 font-medium text-gray-900 dark:text-white">
                                      {txn.reference_number || '-'}
                                    </td>
                                    <td className="py-3 text-gray-600 dark:text-gray-400">
                                      {txn.transaction_date ? new Date(txn.transaction_date).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="py-3 text-gray-600 dark:text-gray-400">
                                      {txn.due_date ? new Date(txn.due_date).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="py-3 text-right font-medium text-gray-900 dark:text-white pr-4">
                                      £{(txn.total_amount || 0).toFixed(2)}
                                    </td>
                                    <td className="py-3 pl-2">
                                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                                        txn.status === 'paid' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                                        txn.status === 'overdue' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                                        txn.status === 'submitted' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                      }`}>
                                        {txn.status}
                                      </span>
                                    </td>
                                    <td className="py-3 text-right">
                                      <div className="flex justify-end gap-1">
                                        <button
                                          onClick={() => openEditTxn(txn)}
                                          className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition"
                                          title="Edit"
                                        >
                                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                          </svg>
                                        </button>
                                        <button
                                          onClick={() => setDeleteTarget({ type: 'transaction', id: txn.id })}
                                          className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition"
                                          title="Delete"
                                        >
                                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                          </svg>
                                        </button>
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        {/* Pagination Footer */}
                        {filteredTransactions.length > 0 && (
                          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                            {/* Page Size Selector */}
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                              <span>Show</span>
                              <select
                                value={itemsPerPage}
                                onChange={(e) => setItemsPerPage(Number(e.target.value))}
                                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                              >
                                {PAGE_SIZE_OPTIONS.map((size) => (
                                  <option key={size} value={size}>
                                    {size}
                                  </option>
                                ))}
                              </select>
                              <span>per page</span>
                            </div>

                            {/* Pagination Controls */}
                            {totalPages > 1 && (
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => setCurrentPage(1)}
                                  disabled={currentPage === 1}
                                  className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="First page"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7m0 0l7-7m-7 7h18" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                                  disabled={currentPage === 1}
                                  className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Previous page"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                  </svg>
                                </button>
                                <span className="text-sm text-gray-600 dark:text-gray-400 px-2">
                                  Page {currentPage} of {totalPages}
                                </span>
                                <button
                                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                                  disabled={currentPage === totalPages}
                                  className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Next page"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => setCurrentPage(totalPages)}
                                  disabled={currentPage === totalPages}
                                  className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Last page"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                                  </svg>
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Accounts Tab */}
                {activeTab === 'accounts' && (
                  <div>
                    {accounts.length === 0 ? (
                      <div className="text-center py-12">
                        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                        </svg>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">No accounts linked</p>
                        <p className="text-sm text-gray-400 dark:text-gray-500">
                          Sync with the client's accounting software to import their chart of accounts
                        </p>
                      </div>
                    ) : (
                      <div>
                        {/* Header with account count and platform info */}
                        <div className="flex items-center justify-between mb-4">
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {accounts.length} accounts from {client?.platform_name || 'accounting software'}
                          </div>
                        </div>

                        {/* Group accounts by type */}
                        {['asset', 'bank', 'liability', 'equity', 'income', 'expense'].map((type) => {
                          const typeAccounts = accounts.filter((a) => a.account_type === type)
                          if (typeAccounts.length === 0) return null

                          const typeColors = {
                            asset: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                            bank: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                            liability: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
                            equity: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
                            income: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300',
                            expense: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
                          }

                          return (
                            <div key={type} className="mb-6">
                              <div className="flex items-center gap-2 mb-3">
                                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                  {type}
                                </h4>
                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColors[type]}`}>
                                  {typeAccounts.length}
                                </span>
                              </div>
                              <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg overflow-hidden">
                                <table className="w-full">
                                  <thead>
                                    <tr className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                      <th className="text-left py-2 px-4 font-medium">Code</th>
                                      <th className="text-left py-2 px-4 font-medium">Name</th>
                                      <th className="text-left py-2 px-4 font-medium hidden md:table-cell">Description</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                                    {typeAccounts.map((account) => (
                                      <tr key={account.id} className="hover:bg-gray-100 dark:hover:bg-gray-700/50">
                                        <td className="py-2 px-4 font-mono text-sm text-gray-900 dark:text-white">
                                          {account.code}
                                        </td>
                                        <td className="py-2 px-4 text-sm text-gray-900 dark:text-white">
                                          {account.name}
                                        </td>
                                        <td className="py-2 px-4 text-sm text-gray-500 dark:text-gray-400 hidden md:table-cell">
                                          {account.description || '-'}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Documents Tab */}
                {activeTab === 'documents' && (
                  <div className="text-center py-12">
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <p className="text-gray-500 dark:text-gray-400 mb-2">Document storage coming soon</p>
                    <p className="text-sm text-gray-400 dark:text-gray-500">
                      Upload receipts, contracts, and other client documents
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - 1 column */}
          <div className="space-y-6">
            {/* Client Details Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Details</h3>
              <div className="space-y-3 text-sm">
                {client?.phone && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Phone</div>
                    <div className="text-gray-900 dark:text-white">{client.phone}</div>
                  </div>
                )}
                {client?.website && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Website</div>
                    <a href={client.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                      {client.website}
                    </a>
                  </div>
                )}
                {(client?.address_line1 || client?.city) && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Address</div>
                    <div className="text-gray-900 dark:text-white">
                      {client?.address_line1 && <div>{client.address_line1}</div>}
                      {client?.address_line2 && <div>{client.address_line2}</div>}
                      {client?.city && <div>{client.city}{client?.postal_code ? `, ${client.postal_code}` : ''}</div>}
                      {client?.country && <div>{client.country}</div>}
                    </div>
                  </div>
                )}
                {client?.tax_number && (
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">VAT Number</div>
                    <div className="text-gray-900 dark:text-white">{client.tax_number}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Pending Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Actions</h3>
              </div>
              <div className="space-y-2">
                {pendingActions.map((action) => (
                  <div
                    key={action.id}
                    className={`p-3 rounded-lg text-sm ${
                      action.priority === 'high'
                        ? 'bg-red-50 dark:bg-red-900/20 border-l-2 border-red-500'
                        : action.priority === 'medium'
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-l-2 border-yellow-500'
                        : 'bg-gray-50 dark:bg-gray-700/50 border-l-2 border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900 dark:text-white">{action.title}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Due {new Date(action.dueDate).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-4 italic">
                AI-powered suggestions coming soon
              </p>
            </div>

            {/* Important Dates */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Key Dates</h3>
              </div>
              <div className="space-y-2">
                {importantDates.map((item) => (
                  <div
                    key={item.id}
                    className={`p-3 rounded-lg flex items-center justify-between text-sm ${
                      item.status === 'overdue'
                        ? 'bg-red-50 dark:bg-red-900/20'
                        : 'bg-gray-50 dark:bg-gray-700/50'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{item.title}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(item.date).toLocaleDateString()}
                      </div>
                    </div>
                    {item.status === 'overdue' && (
                      <span className="text-xs text-red-600 dark:text-red-400 font-medium">Overdue</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      <ClientFormModal
        isOpen={showClientEdit}
        onClose={() => setShowClientEdit(false)}
        onSuccess={fetchClientData}
        client={client}
      />

      <TransactionFormModal
        isOpen={showTxnForm}
        onClose={() => { setShowTxnForm(false); setEditingTxn(null) }}
        onSuccess={fetchClientData}
        transaction={editingTxn}
        clientId={clientId}
        clients={client ? [client] : []}
      />

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleteLoading}
        title={deleteTarget?.type === 'client' ? 'Deactivate Client' : 'Delete Transaction'}
        message={
          deleteTarget?.type === 'client'
            ? `Are you sure you want to deactivate ${client?.name}? This will mark the client as inactive.`
            : 'Are you sure you want to delete this transaction? This action cannot be undone.'
        }
        confirmLabel={deleteTarget?.type === 'client' ? 'Deactivate' : 'Delete'}
      />
    </div>
  )
}
