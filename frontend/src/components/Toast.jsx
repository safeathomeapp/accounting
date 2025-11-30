import { useToastStore } from '../stores/toastStore'

function ToastItem({ toast, onRemove }) {
  const colors = {
    success: 'bg-green-100 border-green-400 text-green-700',
    error: 'bg-red-100 border-red-400 text-red-700',
    info: 'bg-blue-100 border-blue-400 text-blue-700',
    warning: 'bg-yellow-100 border-yellow-400 text-yellow-700',
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
