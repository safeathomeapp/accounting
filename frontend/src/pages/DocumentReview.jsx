import { useMemo, useState } from 'react'
import Navigation from '../components/Navigation'
import { documentsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'

const VAT_CODES = [
  { value: 'VAT20', label: 'VAT 20%', rate: 0.2 },
  { value: 'VAT5', label: 'VAT 5%', rate: 0.05 },
  { value: 'VAT0', label: 'VAT 0%', rate: 0 },
  { value: 'EXEMPT', label: 'Exempt', rate: 0 },
]

const NOMINAL_CODES = [
  { value: '4000', label: '4000 - Sales' },
  { value: '5000', label: '5000 - Cost of Sales' },
  { value: '6100', label: '6100 - Office Supplies' },
  { value: '7000', label: '7000 - Professional Fees' },
]

const emptyLine = (lineNo) => ({
  line_no: lineNo,
  description: '',
  qty: '1',
  unit_price: '0.00',
  net: '0.00',
  vat: '0.00',
  gross: '0.00',
  vat_code: 'VAT20',
  nominal_code: '4000',
  confidence: null,
})

const toNumber = (value) => {
  const parsed = parseFloat(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const formatMoney = (value) => value.toFixed(2)

const getVatRate = (code) => VAT_CODES.find((item) => item.value === code)?.rate ?? 0

const recalcLine = (line) => {
  const qty = toNumber(line.qty)
  const unit = toNumber(line.unit_price)
  const net = qty * unit
  const vat = net * getVatRate(line.vat_code)
  const gross = net + vat
  return {
    ...line,
    net: formatMoney(net),
    vat: formatMoney(vat),
    gross: formatMoney(gross),
  }
}

export default function DocumentReview() {
  const { addToast } = useToastStore()
  const [uploading, setUploading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [draft, setDraft] = useState(null)
  const [inboxItem, setInboxItem] = useState(null)
  const [form, setForm] = useState({
    doc_type: '',
    counterparty_name: '',
    doc_date: '',
    due_date: '',
    currency: 'GBP',
    invoice_no: '',
  })
  const [lines, setLines] = useState([recalcLine(emptyLine(1)), recalcLine(emptyLine(2))])

  const totals = useMemo(() => {
    const net = lines.reduce((sum, line) => sum + toNumber(line.net), 0)
    const vat = lines.reduce((sum, line) => sum + toNumber(line.vat), 0)
    const gross = lines.reduce((sum, line) => sum + toNumber(line.gross), 0)
    return {
      net: formatMoney(net),
      vat: formatMoney(vat),
      gross: formatMoney(gross),
    }
  }, [lines])

  const validationStatus = draft?.validation_json?.status || 'ok'
  const validationIssues = draft?.validation_json?.issues || []

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const uploadResponse = await documentsAPI.upload(file)
      const uploadData = uploadResponse.data
      setInboxItem({
        id: uploadData.inbox_item_id,
        file_name: uploadData.file_name,
        mime_type: uploadData.mime_type,
        file_url: uploadData.file_url,
      })
      setDraft(null)
      addToast('Document uploaded. Ready to run extraction.', 'success')
    } catch (error) {
      console.error(error)
      addToast(error.response?.data?.detail || 'Failed to upload document', 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleExtract = async () => {
    if (!inboxItem?.id) return
    setExtracting(true)
    try {
      const extractResponse = await documentsAPI.extract(inboxItem.id)
      const extractedDraft = extractResponse.data.draft
      setDraft(extractedDraft)
      setInboxItem(extractedDraft.inbox_item)
      setForm({
        doc_type: extractedDraft.doc_type_confirmed || extractedDraft.doc_type_guess || '',
        counterparty_name: extractedDraft.counterparty_guess || '',
        doc_date: extractedDraft.doc_date_confirmed || extractedDraft.doc_date_guess || '',
        due_date: extractedDraft.draft_json?.header?.due_date || '',
        currency: extractedDraft.currency_confirmed || extractedDraft.currency_guess || 'GBP',
        invoice_no: extractedDraft.invoice_no_confirmed || extractedDraft.invoice_no_guess || '',
      })
      const nextLines = extractedDraft.lines?.length
        ? extractedDraft.lines.map((line, idx) => recalcLine({
          line_no: idx + 1,
          description: line.description_confirmed || line.description_guess || '',
          qty: line.qty || '1.00',
          unit_price: line.unit_price || '0.00',
          net: line.net || '0.00',
          vat: line.vat || '0.00',
          gross: line.gross || '0.00',
          vat_code: line.vat_code_confirmed || line.vat_code_guess || 'VAT20',
          nominal_code: line.nominal_code_confirmed || line.nominal_code_guess || '4000',
          confidence: line.confidence,
        }))
        : [recalcLine(emptyLine(1))]
      setLines(nextLines)
      addToast('Extraction completed. Draft loaded.', 'success')
    } catch (error) {
      console.error(error)
      addToast(error.response?.data?.detail || 'Failed to extract document', 'error')
    } finally {
      setExtracting(false)
    }
  }

  const updateLine = (index, key, value) => {
    setLines((prev) => {
      const updated = [...prev]
      const line = { ...updated[index], [key]: value }
      updated[index] = recalcLine(line)
      return updated.map((item, idx) => ({ ...item, line_no: idx + 1 }))
    })
  }

  const addLine = () => {
    setLines((prev) => [...prev, recalcLine(emptyLine(prev.length + 1))])
  }

  const removeLine = (index) => {
    setLines((prev) => prev.filter((_, idx) => idx !== index).map((item, idx) => ({
      ...item,
      line_no: idx + 1,
    })))
  }

  const buildPayload = () => ({
    doc_type: form.doc_type || null,
    counterparty_name: form.counterparty_name || null,
    counterparty_id: null,
    doc_date: form.doc_date || null,
    due_date: form.due_date || null,
    currency: form.currency || null,
    invoice_no: form.invoice_no || null,
    totals: {
      net: totals.net,
      vat: totals.vat,
      gross: totals.gross,
    },
    lines: lines.map((line) => ({
      line_no: line.line_no,
      description: line.description || null,
      qty: line.qty,
      unit_price: line.unit_price,
      net: line.net,
      vat: line.vat,
      gross: line.gross,
      vat_code: line.vat_code || null,
      nominal_code: line.nominal_code || null,
      confidence: line.confidence,
    })),
  })

  const handleSave = async () => {
    if (!draft) return
    setSaving(true)
    try {
      const response = await documentsAPI.saveDraft(draft.id, buildPayload())
      setDraft(response.data.draft)
      setInboxItem(response.data.draft.inbox_item)
      addToast('Draft saved', 'success')
    } catch (error) {
      console.error(error)
      addToast(error.response?.data?.detail || 'Failed to save draft', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = async () => {
    if (!draft) return
    setSubmitting(true)
    try {
      const response = await documentsAPI.submitDraft(draft.id, buildPayload())
      setDraft(response.data.draft)
      setInboxItem(response.data.draft.inbox_item)
      addToast('Draft submitted (internal transaction created)', 'success')
    } catch (error) {
      console.error(error)
      addToast(error.response?.data?.detail || 'Failed to submit draft', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Navigation />

      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Document Review</h1>
              <p className="text-gray-600 dark:text-gray-400">
                Upload a document, run extraction, review fields, and submit a draft.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Upload</span>
                <input
                  type="file"
                  onChange={handleFileChange}
                  className="block text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                  disabled={uploading}
                />
              </label>
              <button
                type="button"
                onClick={handleExtract}
                disabled={!inboxItem?.id || extracting}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {extracting ? 'Extracting...' : 'Run Extraction'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Document Preview</h2>
            {inboxItem?.file_url ? (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden h-[540px]">
                <iframe
                  title="document-preview"
                  src={inboxItem.file_url}
                  className="w-full h-full"
                />
              </div>
            ) : (
              <div className="flex items-center justify-center h-[540px] border border-dashed border-gray-300 dark:border-gray-700 rounded-lg text-gray-500 dark:text-gray-400">
                {uploading ? 'Uploading...' : 'Upload a document to preview'}
              </div>
            )}
            {inboxItem?.file_name && (
              <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                {inboxItem.file_name}
              </p>
            )}
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Draft Details</h2>
              <div className="flex items-center gap-2">
                {draft && (
                  <span className="px-3 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
                    {draft.status || 'draft'}
                  </span>
                )}
                <span
                  className={`px-3 py-1 text-xs rounded-full ${
                    validationStatus === 'ok'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                  }`}
                >
                  {validationStatus === 'ok'
                    ? 'Totals OK'
                    : `Totals Check (${validationIssues.length})`}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Document Type</label>
                <select
                  value={form.doc_type}
                  onChange={(e) => setForm((prev) => ({ ...prev, doc_type: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Select</option>
                  <option value="invoice">Invoice</option>
                  <option value="bill">Bill</option>
                  <option value="receipt">Receipt</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Counterparty</label>
                <input
                  type="text"
                  value={form.counterparty_name}
                  onChange={(e) => setForm((prev) => ({ ...prev, counterparty_name: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Vendor or customer"
                />
              </div>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Document Date</label>
                <input
                  type="date"
                  value={form.doc_date || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, doc_date: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Due Date (optional)</label>
                <input
                  type="date"
                  value={form.due_date || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, due_date: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Currency</label>
                <select
                  value={form.currency}
                  onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="GBP">GBP</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Invoice #</label>
                <input
                  type="text"
                  value={form.invoice_no}
                  onChange={(e) => setForm((prev) => ({ ...prev, invoice_no: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="INV-1001"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Line Items</h3>
                <button
                  type="button"
                  onClick={addLine}
                  className="text-sm px-3 py-1 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                >
                  Add line
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-gray-500 dark:text-gray-400">
                    <tr className="text-left">
                      <th className="py-2 pr-2">Description</th>
                      <th className="py-2 pr-2">Qty</th>
                      <th className="py-2 pr-2">Unit</th>
                      <th className="py-2 pr-2">VAT Code</th>
                      <th className="py-2 pr-2">Nominal</th>
                      <th className="py-2 pr-2 text-right">Net</th>
                      <th className="py-2 pr-2 text-right">VAT</th>
                      <th className="py-2 pr-2 text-right">Gross</th>
                      <th className="py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-800 dark:text-gray-200">
                    {lines.map((line, index) => (
                      <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                        <td className="py-2 pr-2">
                          <input
                            type="text"
                            value={line.description}
                            onChange={(e) => updateLine(index, 'description', e.target.value)}
                            className="w-48 px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-700"
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <input
                            type="number"
                            min="0"
                            step="1"
                            value={line.qty}
                            onChange={(e) => updateLine(index, 'qty', e.target.value)}
                            className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-700"
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={line.unit_price}
                            onChange={(e) => updateLine(index, 'unit_price', e.target.value)}
                            className="w-24 px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-700"
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <select
                            value={line.vat_code}
                            onChange={(e) => updateLine(index, 'vat_code', e.target.value)}
                            className="w-28 px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-700"
                          >
                            {VAT_CODES.map((code) => (
                              <option key={code.value} value={code.value}>{code.label}</option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 pr-2">
                          <select
                            value={line.nominal_code}
                            onChange={(e) => updateLine(index, 'nominal_code', e.target.value)}
                            className="w-32 px-2 py-1 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-700"
                          >
                            {NOMINAL_CODES.map((code) => (
                              <option key={code.value} value={code.value}>{code.label}</option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 pr-2 text-right">{line.net}</td>
                        <td className="py-2 pr-2 text-right">{line.vat}</td>
                        <td className="py-2 pr-2 text-right">{line.gross}</td>
                        <td className="py-2 text-right">
                          <button
                            type="button"
                            onClick={() => removeLine(index)}
                            className="text-xs text-red-600 hover:text-red-700"
                            disabled={lines.length <= 1}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="flex justify-end text-sm text-gray-700 dark:text-gray-300">
                <div className="w-56 space-y-1">
                  <div className="flex justify-between">
                    <span>Net</span>
                    <span>{totals.net}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>VAT</span>
                    <span>{totals.vat}</span>
                  </div>
                  <div className="flex justify-between font-semibold text-gray-900 dark:text-white">
                    <span>Gross</span>
                    <span>{totals.gross}</span>
                  </div>
                </div>
              </div>
            </div>

            {validationIssues.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 text-amber-800 text-sm p-3 dark:border-amber-800/50 dark:bg-amber-900/20 dark:text-amber-200">
                <p className="font-semibold mb-1">Validation issues</p>
                <ul className="list-disc list-inside space-y-1">
                  {validationIssues.map((issue, idx) => (
                    <li key={idx}>{issue.message}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleSave}
                disabled={!draft || saving}
                className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-60 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
              >
                {saving ? 'Saving...' : 'Save Draft'}
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!draft || submitting}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
