import { useToastStore } from '../stores/toastStore'

function ToastItem({ toast, onRemove }) {
  const colors = {
    success: 'bg-green-100 dark:bg-green-900 border-green-400 dark:border-green-700 text-green-700 dark:text-green-300',
    error: 'bg-red-100 dark:bg-red-900 border-red-400 dark:border-red-700 text-red-700 dark:text-red-300',
    info: 'bg-blue-100 dark:bg-blue-900 border-blue-400 dark:border-blue-700 text-blue-700 dark:text-blue-300',
    warning: 'bg-yellow-100 dark:bg-yellow-900 border-yellow-400 dark:border-yellow-700 text-yellow-700 dark:text-yellow-300',
  }

  return (
    <div className={`p-4 border rounded-lg mb-2 flex justify-between items-center ${colors[toast.type]}`}>
      <span>{toast.message}</span>
      <button onClick={() => onRemove(toast.id)} className="text-lg font-bold opacity-60 hover:opacity-100">
        ×
      </button>
    </div>
  )
}

export default function Toast() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 max-w-sm z-50">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>
  )
}
