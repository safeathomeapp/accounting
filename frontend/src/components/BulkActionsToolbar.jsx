export default function BulkActionsToolbar({
  count,
  onSelectAll,
  onDeselectAll,
  isAllSelected,
  totalCount,
  onCategorize,
  onChangeStatus,
  onDelete,
  loading,
}) {
  return (
    <div className="bg-blue-50 border-b border-blue-200 p-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="font-semibold text-blue-900">
          {count} selected {count === totalCount ? '(all)' : `of ${totalCount}`}
        </span>
        <button
          onClick={isAllSelected ? onDeselectAll : onSelectAll}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {isAllSelected ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="flex gap-2">
        <select
          onChange={(e) => {
            if (e.target.value) onCategorize(e.target.value)
            e.target.value = ''
          }}
          disabled={loading}
          className="px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <option value="">Categorize...</option>
          <option value="Office Expenses">Office Expenses</option>
          <option value="Utilities">Utilities</option>
          <option value="Travel & Transport">Travel & Transport</option>
          <option value="Client Entertainment">Client Entertainment</option>
          <option value="Software & Subscriptions">Software & Subscriptions</option>
        </select>

        <select
          onChange={(e) => {
            if (e.target.value) onChangeStatus(e.target.value)
            e.target.value = ''
          }}
          disabled={loading}
          className="px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <option value="">Change Status...</option>
          <option value="Categorized">Categorized</option>
          <option value="Needs Review">Needs Review</option>
          <option value="Pending">Pending</option>
        </select>

        <button
          onClick={onDelete}
          disabled={loading}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Delete'}
        </button>
      </div>
    </div>
  )
}
