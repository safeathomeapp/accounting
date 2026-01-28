import { useState, useEffect } from 'react'
import Modal from './Modal'
import { TextInput, SelectInput } from './FormField'
import { clientsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'

const EMPTY = {
  name: '',
  email: '',
  phone: '',
  website: '',
  industry: '',
  contact_type: 'customer',
  tax_number: '',
  address_line1: '',
  address_line2: '',
  city: '',
  postal_code: '',
  country: '',
}

export default function ClientFormModal({ isOpen, onClose, onSuccess, client = null }) {
  const { addToast } = useToastStore()
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const isEdit = !!client

  useEffect(() => {
    if (isOpen) {
      setForm(client ? { ...EMPTY, ...client } : EMPTY)
      setErrors({})
    }
  }, [isOpen, client])

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSaving(true)
    try {
      if (isEdit) {
        await clientsAPI.update(client.id, form)
        addToast('Client updated', 'success')
      } else {
        await clientsAPI.create(form)
        addToast('Client created', 'success')
      }
      onSuccess?.()
      onClose()
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save client', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? 'Edit Client' : 'New Client'} maxWidth="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name - full width */}
        <TextInput label="Name" required value={form.name} onChange={set('name')} error={errors.name} />

        {/* 2-col rows */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput label="Email" type="email" value={form.email} onChange={set('email')} />
          <TextInput label="Phone" value={form.phone} onChange={set('phone')} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput label="Website" value={form.website} onChange={set('website')} />
          <TextInput label="Industry" value={form.industry} onChange={set('industry')} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            label="Contact Type"
            value={form.contact_type}
            onChange={set('contact_type')}
            options={[
              { value: 'customer', label: 'Customer' },
              { value: 'supplier', label: 'Supplier' },
              { value: 'both', label: 'Both' },
            ]}
          />
          <TextInput label="Tax Number" value={form.tax_number} onChange={set('tax_number')} />
        </div>

        {/* Address */}
        <TextInput label="Address Line 1" value={form.address_line1} onChange={set('address_line1')} />
        <TextInput label="Address Line 2" value={form.address_line2} onChange={set('address_line2')} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TextInput label="City" value={form.city} onChange={set('city')} />
          <TextInput label="Postal Code" value={form.postal_code} onChange={set('postal_code')} />
          <TextInput label="Country" value={form.country} onChange={set('country')} />
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
            {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Client'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
