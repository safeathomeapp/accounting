import { useState, useEffect } from 'react'
import Modal from './Modal'
import { TextInput, SelectInput, NumberInput, DateInput, TextArea } from './FormField'
import { transactionsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'

const EMPTY = {
  transaction_type: 'invoice',
  status: 'draft',
  client_id: '',
  reference_number: '',
  transaction_date: '',
  due_date: '',
  description: '',
  amount: '',
  tax_amount: '',
  currency: 'GBP',
}

export default function TransactionFormModal({
  isOpen,
  onClose,
  onSuccess,
  transaction = null,
  clientId = '',
  clients = [],
}) {
  const { addToast } = useToastStore()
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const isEdit = !!transaction

  useEffect(() => {
    if (isOpen) {
      if (transaction) {
        setForm({
          ...EMPTY,
          ...transaction,
          amount: transaction.amount ?? '',
          tax_amount: transaction.tax_amount ?? '',
          transaction_date: transaction.transaction_date?.slice(0, 10) || '',
          due_date: transaction.due_date?.slice(0, 10) || '',
          client_id: transaction.client_id || '',
        })
      } else {
        setForm({ ...EMPTY, client_id: clientId })
      }
      setErrors({})
    }
  }, [isOpen, transaction, clientId])

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))
  const setNum = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const totalAmount = (parseFloat(form.amount) || 0) + (parseFloat(form.tax_amount) || 0)

  const validate = () => {
    const errs = {}
    if (!form.transaction_date) errs.transaction_date = 'Date is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSaving(true)
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount) || 0,
        tax_amount: parseFloat(form.tax_amount) || 0,
        total_amount: totalAmount,
        client_id: form.client_id || null,
      }

      if (isEdit) {
        await transactionsAPI.update(transaction.id, payload)
        addToast('Transaction updated', 'success')
      } else {
        await transactionsAPI.create(payload)
        addToast('Transaction created', 'success')
      }
      onSuccess?.()
      onClose()
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save transaction', 'error')
    } finally {
      setSaving(false)
    }
  }

  const clientOptions = clients.map((c) => ({ value: c.id, label: c.name }))

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? 'Edit Transaction' : 'New Transaction'} maxWidth="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Row 1: Type + Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            label="Transaction Type"
            value={form.transaction_type}
            onChange={set('transaction_type')}
            options={[
              { value: 'invoice', label: 'Invoice' },
              { value: 'bill', label: 'Bill' },
              { value: 'payment', label: 'Payment' },
              { value: 'receipt', label: 'Receipt' },
            ]}
          />
          <SelectInput
            label="Status"
            value={form.status}
            onChange={set('status')}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'submitted', label: 'Submitted' },
              { value: 'authorised', label: 'Authorised' },
              { value: 'paid', label: 'Paid' },
            ]}
          />
        </div>

        {/* Row 2: Client + Reference */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            label="Client"
            value={form.client_id}
            onChange={set('client_id')}
            placeholder="Select client..."
            options={clientOptions}
          />
          <TextInput label="Reference" value={form.reference_number} onChange={set('reference_number')} />
        </div>

        {/* Row 3: Dates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DateInput label="Date" required value={form.transaction_date} onChange={set('transaction_date')} error={errors.transaction_date} />
          <DateInput label="Due Date" value={form.due_date} onChange={set('due_date')} />
        </div>

        {/* Description */}
        <TextArea label="Description" value={form.description} onChange={set('description')} />

        {/* Row 4: Amounts */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <NumberInput label="Amount" prefix="£" value={form.amount} onChange={setNum('amount')} />
          <NumberInput label="Tax Amount" prefix="£" value={form.tax_amount} onChange={setNum('tax_amount')} />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Total</label>
            <div className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-900 dark:text-white">
              £{totalAmount.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Currency */}
        <div className="w-48">
          <SelectInput
            label="Currency"
            value={form.currency}
            onChange={set('currency')}
            options={['GBP', 'USD', 'EUR']}
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition disabled:opacity-50"
          >
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Transaction'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
