/**
 * Transaction List Page
 *
 * Displays transactions from PostgreSQL database with filtering,
 * sorting, pagination, and bulk operations.
 *
 * @author Claude Code
 * @updated January 24, 2026
 */

import { useState, useEffect } from 'react'
import { useToastStore } from '../stores/toastStore'
import { transactionsAPI } from '../services/api'
import Navigation from '../components/Navigation'
import Pagination from '../components/Pagination'
import DateRangeFilter from '../components/DateRangeFilter'
import BulkActionsToolbar from '../components/BulkActionsToolbar'
import { SkeletonTable } from '../components/Skeleton'
import { exportToCSV } from '../utils/csvExport'
import { useBulkSelection } from '../hooks/useBulkSelection'
import { useSortedItems } from '../hooks/useSortedItems'

const ITEMS_PER_PAGE = 10

export default function TransactionList() {
  const { addToast } = useToastStore()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const bulk = useBulkSelection(transactions)

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await transactionsAPI.list({ limit: 500 })
      const data = response.data

      // Transform backend data to frontend format
      const transformed = (data.transactions || []).map((t) => ({
        id: t.id,
        description: t.description || 'No description',
        amount: t.total_amount || t.amount || 0,
        category: t.account_name || t.transaction_type || 'Uncategorized',
        date: t.transaction_date,
        status: formatStatus(t.status),
        merchant: t.client_name || 'Unknown',
        type: t.transaction_type,
        reference: t.reference_number,
        isReconciled: t.is_reconciled,
      }))

      setTransactions(transformed)
      setTotalCount(data.total || transformed.length)
    } catch (err) {
      console.error('Error fetching transactions:', err)
      setError(err.response?.data?.detail || 'Failed to load transactions')
      addToast('Failed to load transactions', 'error')
    } finally {
      setLoading(false)
    }
  }

  const formatStatus = (status) => {
    if (!status) return 'Pending'
    const statusMap = {
      paid: 'Categorized',
      draft: 'Pending',
      submitted: 'Needs Review',
      authorised: 'Categorized',
      voided: 'Voided',
    }
    return statusMap[status.toLowerCase()] || status
  }

  const filteredTransactions = transactions.filter((t) => {
    const matchesSearch =
      !search ||
      t.description.toLowerCase().includes(search.toLowerCase()) ||
      t.merchant.toLowerCase().includes(search.toLowerCase()) ||
      (t.reference && t.reference.toLowerCase().includes(search.toLowerCase()))
    const matchesType = !typeFilter || t.type === typeFilter
    const matchesStatus = !statusFilter || t.status === statusFilter
    const transactionDate = t.date ? new Date(t.date) : null
    const matchesStartDate = !startDate || (transactionDate && transactionDate >= new Date(startDate))
    const matchesEndDate = !endDate || (transactionDate && transactionDate <= new Date(endDate))
    return matchesSearch && matchesType && matchesStatus && matchesStartDate && matchesEndDate
  })

  const sort = useSortedItems(filteredTransactions)
  const sortedTransactions = sort.getSorted()

  const paginatedTransactions = sortedTransactions.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const handleFilterChange = () => setCurrentPage(1)

  const handlePageChange = (page) => setCurrentPage(page)

  useEffect(() => {
    handleFilterChange()
  }, [search, typeFilter, statusFilter, startDate, endDate])

  const handleResetDates = () => {
    setStartDate('')
    setEndDate('')
  }

  const handleExport = () => {
    exportToCSV(filteredTransactions, 'transactions', [
      { key: 'date', label: 'Date' },
      { key: 'description', label: 'Description' },
      { key: 'merchant', label: 'Client' },
      { key: 'category', label: 'Account' },
      { key: 'type', label: 'Type' },
      { key: 'amount', label: 'Amount' },
      { key: 'status', label: 'Status' },
    ])
    addToast('Transactions exported successfully!', 'success')
  }

  const handleBulkCategorize = async (category) => {
    setBulkLoading(true)
    try {
      const selected = bulk.getSelectedItems()
      // Update local state for immediate feedback
      setTransactions((prev) =>
        prev.map((t) => (selected.find((s) => s.id === t.id) ? { ...t, category } : t))
      )
      bulk.deselectAll()
      addToast(`${selected.length} transactions categorized as ${category}`, 'success')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkStatusChange = async (status) => {
    setBulkLoading(true)
    try {
      const selected = bulk.getSelectedItems()
      const ids = selected.map((t) => t.id)

      // Map frontend status to backend status
      const backendStatusMap = {
        Categorized: 'paid',
        'Needs Review': 'submitted',
        Pending: 'draft',
      }
      const backendStatus = backendStatusMap[status] || status.toLowerCase()

      // Call backend API
      await transactionsAPI.bulkUpdateStatus(ids, backendStatus)

      // Update local state
      setTransactions((prev) =>
        prev.map((t) => (selected.find((s) => s.id === t.id) ? { ...t, status } : t))
      )
      bulk.deselectAll()
      addToast(`${selected.length} transactions status updated to ${status}`, 'success')
    } catch (err) {
      console.error('Error updating status:', err)
      addToast('Failed to update transaction status', 'error')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${bulk.count} transactions?`)) return
    setBulkLoading(true)
    try {
      const selected = bulk.getSelectedItems()
      const ids = selected.map((t) => t.id)

      // Call backend API
      await transactionsAPI.bulkDelete(ids)

      // Update local state
      setTransactions((prev) => prev.filter((t) => !selected.find((s) => s.id === t.id)))
      bulk.deselectAll()
      addToast(`${selected.length} transactions deleted`, 'success')
    } catch (err) {
      console.error('Error deleting transactions:', err)
      addToast('Failed to delete transactions', 'error')
    } finally {
      setBulkLoading(false)
    }
  }

  // Get unique transaction types for filter dropdown
  const transactionTypes = [...new Set(transactions.map((t) => t.type).filter(Boolean))]

  if (error && transactions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md text-center">
            <div className="text-red-600 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Unable to Load Transactions
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
            <button
              onClick={fetchTransactions}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading && transactions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Transactions</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <SkeletonTable rows={5} />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 dark:text-white">
      <Navigation />

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Transactions</h1>
            <p className="text-gray-600 dark:text-gray-300">
              {totalCount.toLocaleString()} transactions from database
            </p>
          </div>
          <button
            onClick={handleExport}
            disabled={filteredTransactions.length === 0}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Export CSV
          </button>
        </div>
      </header>

      {/* Bulk Actions Toolbar */}
      {bulk.hasSelection && (
        <BulkActionsToolbar
          count={bulk.count}
          totalCount={transactions.length}
          isAllSelected={bulk.isAllSelected}
          onSelectAll={bulk.selectAll}
          onDeselectAll={bulk.deselectAll}
          onCategorize={handleBulkCategorize}
          onChangeStatus={handleBulkStatusChange}
          onDelete={handleBulkDelete}
          loading={bulkLoading}
        />
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search description, client, reference..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Transaction Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">All Types</option>
                {transactionTypes.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">All Statuses</option>
                <option value="Categorized">Categorized</option>
                <option value="Needs Review">Needs Review</option>
                <option value="Pending">Pending</option>
              </select>
            </div>
          </div>
        </div>

        {/* Date Range Filter */}
        <DateRangeFilter
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
          onReset={handleResetDates}
        />

        {/* Transactions Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              No transactions found matching your filters
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={bulk.isAllSelected}
                        onChange={(e) => (e.target.checked ? bulk.selectAll() : bulk.deselectAll())}
                        className="w-4 h-4 cursor-pointer"
                      />
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('date')}
                    >
                      Date {sort.getSortIndicator('date')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('description')}
                    >
                      Description {sort.getSortIndicator('description')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('merchant')}
                    >
                      Client {sort.getSortIndicator('merchant')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('type')}
                    >
                      Type {sort.getSortIndicator('type')}
                    </th>
                    <th
                      className="px-6 py-3 text-right text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('amount')}
                    >
                      Amount {sort.getSortIndicator('amount')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                      onClick={() => sort.toggleSort('status')}
                    >
                      Status {sort.getSortIndicator('status')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-gray-700">
                  {paginatedTransactions.map((transaction) => (
                    <tr
                      key={transaction.id}
                      className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${
                        bulk.isItemSelected(transaction.id) ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                      }`}
                    >
                      <td className="px-4 py-4 text-center">
                        <input
                          type="checkbox"
                          checked={bulk.isItemSelected(transaction.id)}
                          onChange={() => bulk.toggleItem(transaction.id)}
                          className="w-4 h-4 cursor-pointer"
                        />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {transaction.date
                          ? new Date(transaction.date).toLocaleDateString()
                          : 'No date'}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                        {transaction.description}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {transaction.merchant}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            transaction.type === 'invoice'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                              : transaction.type === 'bill'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {transaction.type
                            ? transaction.type.charAt(0).toUpperCase() + transaction.type.slice(1)
                            : 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-right text-gray-900 dark:text-white">
                        £{transaction.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            transaction.status === 'Categorized'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                              : transaction.status === 'Needs Review'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {transaction.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {filteredTransactions.length > ITEMS_PER_PAGE && (
          <Pagination
            currentPage={currentPage}
            totalItems={filteredTransactions.length}
            itemsPerPage={ITEMS_PER_PAGE}
            onPageChange={handlePageChange}
          />
        )}

        {/* Summary */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">
              Filtered Transactions
            </p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              {filteredTransactions.length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Total Amount</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
              £{filteredTransactions.reduce((sum, t) => sum + t.amount, 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">Categorized</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">
              {filteredTransactions.filter((t) => t.status === 'Categorized').length}
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
