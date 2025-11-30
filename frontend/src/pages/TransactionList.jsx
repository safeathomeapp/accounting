import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useToastStore } from '../stores/toastStore'
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
  const navigate = useNavigate()
  const { logout } = useAuthStore()
  const { addToast } = useToastStore()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const bulk = useBulkSelection(transactions)

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('authToken')
      const response = await fetch('http://localhost:8000/api/v1/dashboard/transactions', {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        // Use mock data for demo
        setTransactions(generateMockTransactions())
      } else {
        const data = await response.json()
        setTransactions(data.transactions || generateMockTransactions())
      }
      setError(null)
    } catch (err) {
      console.error('Error fetching transactions:', err)
      // Use mock data on error
      setTransactions(generateMockTransactions())
    } finally {
      setLoading(false)
    }
  }

  const generateMockTransactions = () => [
    {
      id: '1',
      description: 'Office Supplies',
      amount: 125.50,
      category: 'Office Expenses',
      date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Categorized',
      merchant: 'Staples',
    },
    {
      id: '2',
      description: 'Internet Payment',
      amount: 79.99,
      category: 'Utilities',
      date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Categorized',
      merchant: 'BT Internet',
    },
    {
      id: '3',
      description: 'Fuel',
      amount: 60.00,
      category: 'Travel & Transport',
      date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Needs Review',
      merchant: 'Shell Petrol',
    },
    {
      id: '4',
      description: 'Coffee Meeting',
      amount: 15.50,
      category: 'Client Entertainment',
      date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Pending',
      merchant: 'Costa Coffee',
    },
    {
      id: '5',
      description: 'Software License',
      amount: 299.00,
      category: 'Software & Subscriptions',
      date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Categorized',
      merchant: 'Adobe Creative Cloud',
    },
  ]

  const filteredTransactions = transactions.filter((t) => {
    const matchesSearch =
      t.description.toLowerCase().includes(search.toLowerCase()) ||
      t.merchant.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = !categoryFilter || t.category === categoryFilter
    const matchesStatus = !statusFilter || t.status === statusFilter
    const transactionDate = new Date(t.date)
    const matchesStartDate = !startDate || transactionDate >= new Date(startDate)
    const matchesEndDate = !endDate || transactionDate <= new Date(endDate)
    return matchesSearch && matchesCategory && matchesStatus && matchesStartDate && matchesEndDate
  })

  const sort = useSortedItems(filteredTransactions)
  const sortedTransactions = sort.getSorted()

  const paginatedTransactions = sortedTransactions.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const handleFilterChange = () => setCurrentPage(1)

  const handlePageChange = (page) => setCurrentPage(page)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  useEffect(() => {
    handleFilterChange()
  }, [search, categoryFilter, statusFilter, startDate, endDate])

  const handleResetDates = () => {
    setStartDate('')
    setEndDate('')
  }

  const handleExport = () => {
    exportToCSV(filteredTransactions, 'transactions', [
      { key: 'date', label: 'Date' },
      { key: 'description', label: 'Description' },
      { key: 'merchant', label: 'Merchant' },
      { key: 'category', label: 'Category' },
      { key: 'amount', label: 'Amount' },
      { key: 'status', label: 'Status' },
    ])
    addToast('Transactions exported successfully!', 'success')
  }

  const handleBulkCategorize = async (category) => {
    setBulkLoading(true)
    try {
      const selected = bulk.getSelectedItems()
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
      setTransactions((prev) =>
        prev.map((t) => (selected.find((s) => s.id === t.id) ? { ...t, status } : t))
      )
      bulk.deselectAll()
      addToast(`${selected.length} transactions status updated to ${status}`, 'success')
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${bulk.count} transactions?`)) return
    setBulkLoading(true)
    try {
      const selected = bulk.getSelectedItems()
      setTransactions((prev) => prev.filter((t) => !selected.find((s) => s.id === t.id)))
      bulk.deselectAll()
      addToast(`${selected.length} transactions deleted`, 'success')
    } finally {
      setBulkLoading(false)
    }
  }

  if (loading && transactions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
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
            <p className="text-gray-600 dark:text-gray-300">View and manage all transactions</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={handleExport}
              disabled={filteredTransactions.length === 0}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              📥 Export CSV
            </button>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
            >
              Logout
            </button>
          </div>
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
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search by description or merchant
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                <option value="Office Expenses">Office Expenses</option>
                <option value="Utilities">Utilities</option>
                <option value="Travel & Transport">Travel & Transport</option>
                <option value="Client Entertainment">Client Entertainment</option>
                <option value="Software & Subscriptions">Software & Subscriptions</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No transactions found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
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
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('date')}
                    >
                      Date {sort.getSortIndicator('date')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('description')}
                    >
                      Description {sort.getSortIndicator('description')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('merchant')}
                    >
                      Merchant {sort.getSortIndicator('merchant')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('category')}
                    >
                      Category {sort.getSortIndicator('category')}
                    </th>
                    <th
                      className="px-6 py-3 text-right text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('amount')}
                    >
                      Amount {sort.getSortIndicator('amount')}
                    </th>
                    <th
                      className="px-6 py-3 text-left text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                      onClick={() => sort.toggleSort('status')}
                    >
                      Status {sort.getSortIndicator('status')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paginatedTransactions.map((transaction) => (
                    <tr key={transaction.id} className={`hover:bg-gray-50 ${bulk.isItemSelected(transaction.id) ? 'bg-blue-50' : ''}`}>
                      <td className="px-4 py-4 text-center">
                        <input
                          type="checkbox"
                          checked={bulk.isItemSelected(transaction.id)}
                          onChange={() => bulk.toggleItem(transaction.id)}
                          className="w-4 h-4 cursor-pointer"
                        />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(transaction.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {transaction.description}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {transaction.merchant}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {transaction.category}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-right text-gray-900">
                        £{transaction.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            transaction.status === 'Categorized'
                              ? 'bg-green-100 text-green-800'
                              : transaction.status === 'Needs Review'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
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
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Total Transactions</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {filteredTransactions.length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Total Amount</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              £{filteredTransactions.reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500 text-sm font-medium">Categorized</p>
            <p className="text-3xl font-bold text-green-600 mt-1">
              {filteredTransactions.filter((t) => t.status === 'Categorized').length}
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
