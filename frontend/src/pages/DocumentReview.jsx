import { useMemo, useState, useRef, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import Navigation from '../components/Navigation'
import { documentsAPI, clientsAPI } from '../services/api'
import { useToastStore } from '../stores/toastStore'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

// Backend base URL for file serving
const BACKEND_BASE = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000'

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
  { value: '7100', label: '7100 - Utilities' },
  { value: '7200', label: '7200 - Travel' },
  { value: '7300', label: '7300 - Subscriptions' },
]

const DOC_TYPES = [
  // AP (Accounts Payable) - vendor sent us this
  { value: 'bill', label: 'Bill (AP)', direction: 'ap' },
  { value: 'credit_note_received', label: 'Credit Note Received (AP)', direction: 'ap' },
  { value: 'purchase_order', label: 'Purchase Order (AP)', direction: 'ap' },
  { value: 'payment_made', label: 'Payment Made (AP)', direction: 'ap' },
  // AR (Accounts Receivable) - we sent this to customer
  { value: 'sales_invoice', label: 'Sales Invoice (AR)', direction: 'ar' },
  { value: 'credit_note_issued', label: 'Credit Note Issued (AR)', direction: 'ar' },
  { value: 'estimate', label: 'Estimate (AR)', direction: 'ar' },
  { value: 'payment_received', label: 'Payment Received (AR)', direction: 'ar' },
]

// Map document type to contact direction for auto-detection
const DOC_TYPE_CONTACT_DIR = {
  bill: 'vendor',
  credit_note_received: 'vendor',
  purchase_order: 'vendor',
  payment_made: 'vendor',
  sales_invoice: 'customer',
  credit_note_issued: 'customer',
  estimate: 'customer',
  payment_received: 'customer',
}

// Map OCR-extracted doc types to canonical types
// OCR may return ambiguous terms like "invoice" - we resolve using contact direction
function normalizeDocType(rawType, contactType) {
  if (!rawType) return ''
  const lower = rawType.toLowerCase().trim()

  // Direct canonical matches
  if (DOC_TYPE_CONTACT_DIR[lower]) return lower

  // Ambiguous "invoice" - determine from contact direction
  if (lower === 'invoice' || lower === 'tax invoice') {
    return contactType === 'customer' ? 'sales_invoice' : 'bill'
  }

  // Common OCR variations
  if (lower.includes('bill') || lower === 'purchase invoice') return 'bill'
  if (lower.includes('sales invoice') || lower === 'sales_invoice') return 'sales_invoice'
  if (lower.includes('credit note') || lower.includes('credit memo')) {
    return contactType === 'customer' ? 'credit_note_issued' : 'credit_note_received'
  }
  if (lower.includes('estimate') || lower.includes('quote') || lower.includes('quotation')) return 'estimate'
  if (lower.includes('purchase order') || lower === 'po') return 'purchase_order'
  if (lower.includes('receipt') || lower.includes('payment received')) return 'payment_received'
  if (lower.includes('payment') || lower.includes('remittance')) return 'payment_made'

  // Default: if we have a vendor contact, assume AP (bill)
  return contactType === 'customer' ? 'sales_invoice' : 'bill'
}

const CURRENCIES = [
  { value: 'GBP', label: 'GBP' },
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'CAD', label: 'CAD' },
  { value: 'AUD', label: 'AUD' },
  { value: 'CHF', label: 'CHF' },
]

const PAYMENT_TERMS = [
  { value: 'immediate', label: 'Due Immediately', days: 0 },
  { value: 'net7', label: 'Net 7', days: 7 },
  { value: 'net14', label: 'Net 14', days: 14 },
  { value: 'net30', label: 'Net 30', days: 30 },
  { value: 'net45', label: 'Net 45', days: 45 },
  { value: 'net60', label: 'Net 60', days: 60 },
  { value: 'net90', label: 'Net 90', days: 90 },
  { value: 'eom', label: 'End of Month', days: null },
  { value: 'custom', label: 'Custom', days: null },
]

/**
 * Parse ambiguous date strings and return possible interpretations
 * Returns array of { value: 'YYYY-MM-DD', label: 'description' }
 */
function parseAmbiguousDate(dateStr) {
  if (!dateStr) return []

  // Already in ISO format
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    const d = new Date(dateStr)
    return [{ value: dateStr, label: formatDateLabel(d) }]
  }

  const interpretations = []
  const now = new Date()
  const currentYear = now.getFullYear()

  // Match various date patterns
  const patterns = [
    // DD/MM/YY or DD-MM-YY or DD.MM.YY
    /^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$/,
  ]

  for (const pattern of patterns) {
    const match = dateStr.match(pattern)
    if (match) {
      let [, p1, p2, p3] = match
      p1 = parseInt(p1, 10)
      p2 = parseInt(p2, 10)
      p3 = parseInt(p3, 10)

      // Handle 2-digit year
      if (p3 < 100) {
        p3 = p3 > 50 ? 1900 + p3 : 2000 + p3
      }

      // Check if ambiguous (both could be day or month)
      const isAmbiguous = p1 <= 12 && p2 <= 12 && p1 !== p2

      if (isAmbiguous) {
        // DD/MM/YYYY interpretation (UK/EU format)
        if (p1 <= 31 && p2 <= 12) {
          const d = new Date(p3, p2 - 1, p1)
          if (isValidDate(d, p1, p2, p3)) {
            interpretations.push({
              value: formatISODate(d),
              label: `${formatDateLabel(d)} (DD/MM)`,
            })
          }
        }
        // MM/DD/YYYY interpretation (US format)
        if (p2 <= 31 && p1 <= 12) {
          const d = new Date(p3, p1 - 1, p2)
          if (isValidDate(d, p2, p1, p3)) {
            interpretations.push({
              value: formatISODate(d),
              label: `${formatDateLabel(d)} (MM/DD)`,
            })
          }
        }
      } else {
        // Unambiguous - determine format based on values
        if (p1 > 12 && p2 <= 12) {
          // DD/MM/YYYY
          const d = new Date(p3, p2 - 1, p1)
          if (isValidDate(d, p1, p2, p3)) {
            interpretations.push({ value: formatISODate(d), label: formatDateLabel(d) })
          }
        } else if (p2 > 12 && p1 <= 12) {
          // MM/DD/YYYY
          const d = new Date(p3, p1 - 1, p2)
          if (isValidDate(d, p2, p1, p3)) {
            interpretations.push({ value: formatISODate(d), label: formatDateLabel(d) })
          }
        } else {
          // Default to DD/MM/YYYY for UK
          const d = new Date(p3, p2 - 1, p1)
          if (isValidDate(d, p1, p2, p3)) {
            interpretations.push({ value: formatISODate(d), label: formatDateLabel(d) })
          }
        }
      }
    }
  }

  // If no pattern matched, try native Date parsing
  if (interpretations.length === 0) {
    const d = new Date(dateStr)
    if (!isNaN(d.getTime())) {
      interpretations.push({ value: formatISODate(d), label: formatDateLabel(d) })
    }
  }

  return interpretations
}

function isValidDate(d, day, month, year) {
  return d.getDate() === day && d.getMonth() === month - 1 && d.getFullYear() === year
}

function formatISODate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatDateLabel(d) {
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

/**
 * Calculate due date from invoice date and payment terms
 */
function calculateDueDate(invoiceDate, terms) {
  if (!invoiceDate || !terms) return null

  const term = PAYMENT_TERMS.find(t => t.value === terms)
  if (!term) return null

  const date = new Date(invoiceDate)
  if (isNaN(date.getTime())) return null

  if (term.value === 'eom') {
    // End of month
    date.setMonth(date.getMonth() + 1, 0)
  } else if (term.days !== null) {
    date.setDate(date.getDate() + term.days)
  } else {
    return null
  }

  return formatISODate(date)
}

/**
 * Parse payment terms string to standardized value
 */
function parsePaymentTerms(termsStr) {
  if (!termsStr) return null
  const lower = termsStr.toLowerCase().replace(/\s+/g, '')

  // Immediate / due on receipt / full payment
  if (lower.includes('immediate') || lower.includes('duereceipt') || lower.includes('dueonreceipt')
    || lower.includes('fullpayment') || lower.includes('payableimmediately') || lower.includes('cod')
    || lower.includes('cashondelivery') || lower === '0days' || lower === '0day') return 'immediate'

  // Net terms - check for explicit numbers
  if (lower.includes('net7') || lower === '7days' || lower === '7day') return 'net7'
  if (lower.includes('net14') || lower === '14days' || lower === '14day') return 'net14'
  if (lower.includes('net30') || lower === '30days' || lower === '30day') return 'net30'
  if (lower.includes('net45') || lower === '45days' || lower === '45day') return 'net45'
  if (lower.includes('net60') || lower === '60days' || lower === '60day') return 'net60'
  if (lower.includes('net90') || lower === '90days' || lower === '90day') return 'net90'
  if (lower.includes('endofmonth') || lower.includes('eom')) return 'eom'

  // Try to extract a number of days from the string
  const daysMatch = termsStr.match(/(\d+)\s*days?/i)
  if (daysMatch) {
    const days = parseInt(daysMatch[1], 10)
    if (days === 0) return 'immediate'
    if (days <= 7) return 'net7'
    if (days <= 14) return 'net14'
    if (days <= 30) return 'net30'
    if (days <= 45) return 'net45'
    if (days <= 60) return 'net60'
    if (days <= 90) return 'net90'
  }

  return 'custom'
}

/**
 * Simple fuzzy match score (0-1) using Levenshtein-like comparison
 */
function fuzzyMatch(str1, str2) {
  if (!str1 || !str2) return 0
  const s1 = str1.toLowerCase().trim()
  const s2 = str2.toLowerCase().trim()

  if (s1 === s2) return 1
  if (s1.includes(s2) || s2.includes(s1)) return 0.9

  // Simple word overlap score
  const words1 = new Set(s1.split(/\s+/).filter(w => w.length > 2))
  const words2 = new Set(s2.split(/\s+/).filter(w => w.length > 2))

  if (words1.size === 0 || words2.size === 0) return 0

  let matches = 0
  for (const w of words1) {
    if (words2.has(w)) matches++
  }

  return matches / Math.max(words1.size, words2.size)
}

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

// Format line without recalculating - preserves OCR-extracted values
const formatLine = (line) => ({
  ...line,
  net: formatMoney(toNumber(line.net)),
  vat: formatMoney(toNumber(line.vat)),
  gross: formatMoney(toNumber(line.gross)),
})

// Confidence threshold below which we show uncertainty indicator
const CONFIDENCE_THRESHOLD = 0.7

/**
 * Editable combobox component for fields with AI uncertainty
 */
function UncertaintyCombobox({
  value,
  onChange,
  options,
  confidence,
  placeholder,
  allowCustom = true,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState(value || '')
  const containerRef = useRef(null)
  const inputRef = useRef(null)

  const isUncertain = confidence !== null && confidence < CONFIDENCE_THRESHOLD

  useEffect(() => {
    setInputValue(value || '')
  }, [value])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredOptions = options.filter(
    (opt) =>
      opt.label.toLowerCase().includes(inputValue.toLowerCase()) ||
      opt.value.toLowerCase().includes(inputValue.toLowerCase())
  )

  const handleSelect = (opt) => {
    setInputValue(opt.label)
    onChange(opt.value)
    setIsOpen(false)
  }

  const handleInputChange = (e) => {
    const newVal = e.target.value
    setInputValue(newVal)
    setIsOpen(true)
    if (allowCustom) {
      onChange(newVal)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && filteredOptions.length > 0) {
      handleSelect(filteredOptions[0])
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`w-full px-3 py-2 pr-8 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${
            isUncertain
              ? 'border-amber-400 dark:border-amber-500 ring-1 ring-amber-200 dark:ring-amber-800'
              : 'border-gray-300 dark:border-gray-600'
          }`}
        />
        {isUncertain && (
          <span
            className="absolute right-2 top-1/2 -translate-y-1/2 text-amber-500 cursor-help"
            title={`AI confidence: ${Math.round((confidence || 0) * 100)}%`}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        )}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          style={{ right: isUncertain ? '28px' : '8px' }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {filteredOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleSelect(opt)}
              className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Authenticated image preview - fetches image with auth headers and displays via blob URL
 */
function AuthImage({ url, alt }) {
  const [blobUrl, setBlobUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!url) return
    let currentBlobUrl = null

    const fetchImage = async () => {
      setLoading(true)
      setError(null)
      try {
        const token = localStorage.getItem('authToken')
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!response.ok) throw new Error(`Failed to load image: ${response.status}`)
        const blob = await response.blob()
        currentBlobUrl = URL.createObjectURL(blob)
        setBlobUrl(currentBlobUrl)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchImage()
    return () => {
      if (currentBlobUrl) URL.revokeObjectURL(currentBlobUrl)
    }
  }, [url])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <p className="text-red-500 mb-2">Unable to load image</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    )
  }

  return <img src={blobUrl} alt={alt} className="max-w-full max-h-full object-contain" />
}

/**
 * PDF preview using react-pdf (PDF.js)
 * Fetches PDF with authentication before rendering
 */
function PDFPreview({ url, fileName }) {
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [pdfData, setPdfData] = useState(null)
  const [blobUrl, setBlobUrl] = useState(null)
  const containerRef = useRef(null)
  const [containerWidth, setContainerWidth] = useState(null)

  // Fetch PDF with authentication
  useEffect(() => {
    if (!url) return

    let currentBlobUrl = null

    const fetchPdf = async () => {
      setLoading(true)
      setLoadError(null)
      setPdfData(null)
      setBlobUrl(null)

      try {
        const token = localStorage.getItem('authToken')
        const response = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })

        if (!response.ok) {
          throw new Error(`Failed to load PDF: ${response.status} ${response.statusText}`)
        }

        const arrayBuffer = await response.arrayBuffer()

        // Create blob from the original buffer for "Open in New Tab"
        const blob = new Blob([arrayBuffer], { type: 'application/pdf' })
        currentBlobUrl = URL.createObjectURL(blob)
        setBlobUrl(currentBlobUrl)

        // Use the blob URL for react-pdf (avoids ArrayBuffer detachment issues)
        setPdfData(currentBlobUrl)
      } catch (error) {
        console.error('PDF fetch error:', error)
        setLoadError(error.message || 'Failed to fetch PDF')
        setLoading(false)
      }
    }

    fetchPdf()

    // Cleanup blob URL on unmount or URL change
    return () => {
      if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl)
      }
    }
  }, [url])

  // Measure container width for responsive scaling
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.clientWidth - 32) // 32px for padding
      }
    }
    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  const onDocumentLoadSuccess = useCallback(({ numPages }) => {
    setNumPages(numPages)
    setLoading(false)
    setLoadError(null)
  }, [])

  const onDocumentLoadError = useCallback((error) => {
    console.error('PDF load error:', error)
    setLoadError(error.message || 'Failed to load PDF')
    setLoading(false)
  }, [])

  const goToPrevPage = () => setPageNumber((prev) => Math.max(prev - 1, 1))
  const goToNextPage = () => setPageNumber((prev) => Math.min(prev + 1, numPages || 1))
  const zoomIn = () => setScale((prev) => Math.min(prev + 0.25, 3))
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.25, 0.5))
  const fitToWidth = () => setScale(1.0)

  if (loadError) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50 dark:bg-gray-800 p-8">
        <svg className="w-16 h-16 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-gray-600 dark:text-gray-400 mb-2">Unable to load PDF</p>
        <p className="text-gray-500 dark:text-gray-500 text-sm mb-4">{loadError}</p>
        <p className="text-gray-400 dark:text-gray-600 text-xs">Please try uploading the document again</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex flex-col h-full">
      {/* PDF Toolbar */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        {/* Page navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Previous page"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-300 min-w-[80px] text-center">
            {loading ? '...' : `${pageNumber} / ${numPages}`}
          </span>
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= (numPages || 1)}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Next page"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            disabled={scale <= 0.5}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40"
            title="Zoom out"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <button
            onClick={fitToWidth}
            className="px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            title="Fit to width"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            onClick={zoomIn}
            disabled={scale >= 3}
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40"
            title="Zoom in"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
        </div>

        {/* Open in new tab - uses blob URL to bypass auth */}
        {blobUrl ? (
          <a
            href={blobUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Open in new tab"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ) : (
          <span className="p-1.5 rounded opacity-40 cursor-not-allowed" title="Loading...">
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </span>
        )}
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-300 dark:bg-gray-900">
        <div className="flex justify-center p-4 min-h-full">
          {(loading || !pdfData) && !loadError && (
            <div className="flex items-center justify-center">
              <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          )}
          {pdfData && (
          <Document
            file={pdfData}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading=""
            className="shadow-xl"
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              width={containerWidth || undefined}
              className="bg-white"
              loading=""
            />
          </Document>
          )}
        </div>
      </div>
    </div>
  )
}

export default function DocumentReview() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const { addToast } = useToastStore()

  // Refs
  const vendorDropdownRef = useRef(null)

  // Client context state
  const [client, setClient] = useState(null)
  const [clientAccounts, setClientAccounts] = useState([])
  const [loadingClient, setLoadingClient] = useState(false)

  const [uploading, setUploading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [draft, setDraft] = useState(null)
  const [inboxItem, setInboxItem] = useState(null)
  const [viewMode, setViewMode] = useState('full') // 'full' or 'compact'
  const [form, setForm] = useState({
    doc_type: '',
    counterparty_name: '',
    doc_date: '',
    due_date: '',
    currency: 'GBP',
    invoice_no: '',
    payment_terms: '',
    order_no: '',
  })
  const [fieldConfidence, setFieldConfidence] = useState({
    doc_type: null,
    counterparty_name: null,
    doc_date: null,
    currency: null,
    invoice_no: null,
  })
  const [lines, setLines] = useState([recalcLine(emptyLine(1)), recalcLine(emptyLine(2))])

  // Persistent document errors - computed once from OCR extraction, never cleared by edits
  // These represent discrepancies found on the original document itself
  const [documentErrors, setDocumentErrors] = useState([])

  // Date interpretation state
  const [dateInterpretations, setDateInterpretations] = useState({ doc_date: [], due_date: [] })
  const [rawDateStrings, setRawDateStrings] = useState({ doc_date: '', due_date: '' })

  // Contact matching state (vendors/customers for this client)
  const [contacts, setContacts] = useState([])
  const [contactMatches, setContactMatches] = useState([])
  const [selectedContact, setSelectedContact] = useState(null)
  const [showContactDropdown, setShowContactDropdown] = useState(false)

  // Extracted vendor/contact details from OCR
  const [extractedVendor, setExtractedVendor] = useState(null)

  // Fetch client data and accounts when clientId is present
  useEffect(() => {
    if (clientId) {
      fetchClientContext()
    }
  }, [clientId])

  const fetchClientContext = async () => {
    setLoadingClient(true)
    try {
      const [clientRes, accountsRes] = await Promise.all([
        clientsAPI.get(clientId),
        clientsAPI.getAccounts(clientId),
      ])
      setClient(clientRes.data)
      setClientAccounts(accountsRes.data.accounts || [])

      // Fetch contacts (vendors/customers) for this client for matching
      try {
        const contactsRes = await clientsAPI.getContacts(clientId, { limit: 500 })
        setContacts(contactsRes.data.contacts || [])
      } catch (e) {
        console.warn('Could not load contacts for matching:', e)
      }
    } catch (error) {
      console.error('Failed to fetch client context:', error)
      addToast('Failed to load client data', 'error')
    } finally {
      setLoadingClient(false)
    }
  }

  // Auto-calculate due date when invoice date or payment terms change
  useEffect(() => {
    if (form.doc_date && form.payment_terms && form.payment_terms !== 'custom') {
      const calculatedDue = calculateDueDate(form.doc_date, form.payment_terms)
      if (calculatedDue && calculatedDue !== form.due_date) {
        setForm(prev => ({ ...prev, due_date: calculatedDue }))
      }
    }
  }, [form.doc_date, form.payment_terms])

  // Find contact matches when counterparty name changes
  useEffect(() => {
    if (form.counterparty_name && contacts.length > 0) {
      const matches = contacts
        .map(c => ({ ...c, score: fuzzyMatch(form.counterparty_name, c.name) }))
        .filter(c => c.score > 0.3)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5)
      setContactMatches(matches)

      // Auto-select if very high confidence match
      if (matches.length > 0 && matches[0].score > 0.95) {
        setSelectedContact(matches[0])
      }
    } else {
      setContactMatches([])
    }
  }, [form.counterparty_name, contacts])

  // Click outside to close contact dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (vendorDropdownRef.current && !vendorDropdownRef.current.contains(event.target)) {
        setShowContactDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Build nominal codes from client accounts (expense/cost accounts for bills)
  const nominalCodeOptions = useMemo(() => {
    if (clientAccounts.length > 0) {
      // Filter to expense-type accounts and format for dropdown
      const expenseAccounts = clientAccounts
        .filter(acc => ['expense', 'cost_of_sales', 'direct_costs'].includes(acc.account_type?.toLowerCase()))
        .map(acc => ({
          value: acc.code,
          label: `${acc.code} - ${acc.name}`,
        }))
      if (expenseAccounts.length > 0) {
        return expenseAccounts
      }
    }
    // Fallback to default codes
    return NOMINAL_CODES
  }, [clientAccounts])

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
  const serverValidationIssues = draft?.validation_json?.issues || []

  // Client-side validation: check current form state for completeness and math
  const { errors: fieldErrors, issues: formIssues } = useMemo(() => {
    if (!draft) return { errors: {}, issues: [] }

    const errors = {}    // { fieldName: true } for red highlighting
    const issues = []    // { field, message, severity } for the form issues panel

    // Header field validation
    if (!form.doc_type) {
      errors.doc_type = true
      issues.push({ field: 'doc_type', message: 'Document type is required', severity: 'error' })
    }
    if (!form.counterparty_name) {
      errors.counterparty_name = true
      issues.push({ field: 'counterparty_name', message: 'Contact name is required', severity: 'error' })
    }
    if (!form.doc_date) {
      errors.doc_date = true
      issues.push({ field: 'doc_date', message: 'Invoice date is required', severity: 'error' })
    }
    if (!form.invoice_no) {
      errors.invoice_no = true
      issues.push({ field: 'invoice_no', message: 'Invoice/reference number is missing', severity: 'warning' })
    }

    // Line item validation (current form values)
    lines.forEach((line, idx) => {
      const lineKey = `line_${idx}`
      const qty = toNumber(line.qty)
      const unitPrice = toNumber(line.unit_price)
      const net = toNumber(line.net)
      const vat = toNumber(line.vat)
      const gross = toNumber(line.gross)
      const vatRate = getVatRate(line.vat_code)

      const expectedNet = qty * unitPrice
      if (Math.abs(expectedNet - net) > 0.02 && net !== 0) {
        errors[`${lineKey}_net`] = true
        issues.push({
          field: lineKey,
          message: `Line ${idx + 1}: Net (${line.net}) ≠ Qty x Unit Price (${formatMoney(expectedNet)})`,
          severity: 'error',
        })
      }

      const expectedVat = net * vatRate
      if (Math.abs(expectedVat - vat) > 0.02 && vat !== 0) {
        errors[`${lineKey}_vat`] = true
        issues.push({
          field: lineKey,
          message: `Line ${idx + 1}: VAT (${line.vat}) ≠ expected (${formatMoney(expectedVat)}) at ${line.vat_code}`,
          severity: 'error',
        })
      }

      const expectedGross = net + vat
      if (Math.abs(expectedGross - gross) > 0.02 && gross !== 0) {
        errors[`${lineKey}_gross`] = true
        issues.push({
          field: lineKey,
          message: `Line ${idx + 1}: Gross (${line.gross}) ≠ Net + VAT (${formatMoney(expectedGross)})`,
          severity: 'error',
        })
      }

      if (net === 0 && line.description) {
        errors[`${lineKey}_net`] = true
        issues.push({ field: lineKey, message: `Line ${idx + 1}: Has description but zero net amount`, severity: 'warning' })
      }
      if (!line.description && net !== 0) {
        errors[`${lineKey}_desc`] = true
        issues.push({ field: lineKey, message: `Line ${idx + 1}: Has amount but no description`, severity: 'warning' })
      }
    })

    // Include server-side validation issues
    serverValidationIssues.forEach(issue => {
      issues.push({ field: 'server', message: issue.message, severity: 'error' })
    })

    // Also mark fields with persistent document errors for red highlighting
    documentErrors.forEach(docErr => {
      if (docErr.lineIndex !== undefined) {
        const lineKey = `line_${docErr.lineIndex}`
        if (docErr.type === 'net_mismatch') errors[`${lineKey}_net`] = true
        if (docErr.type === 'vat_mismatch') errors[`${lineKey}_vat`] = true
        if (docErr.type === 'gross_mismatch') errors[`${lineKey}_gross`] = true
      }
      if (docErr.type === 'total_net_mismatch') errors.total_net = true
      if (docErr.type === 'total_vat_mismatch') errors.total_vat = true
      if (docErr.type === 'total_gross_mismatch') errors.total_gross = true
    })

    return { errors, issues }
  }, [draft, form, lines, serverValidationIssues, documentErrors])

  // Construct full URL for file preview
  const getFileUrl = (fileUrl) => {
    if (!fileUrl) return null
    if (fileUrl.startsWith('http')) return fileUrl
    return `${BACKEND_BASE}${fileUrl}`
  }

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const uploadResponse = await documentsAPI.upload(file, clientId || null)
      const uploadData = uploadResponse.data
      setInboxItem({
        id: uploadData.inbox_item_id,
        file_name: uploadData.file_name,
        mime_type: uploadData.mime_type,
        file_url: uploadData.file_url,
        client_id: uploadData.client_id,
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

      // Extract confidence data from draft_json if available
      const headerConfidence = extractedDraft.draft_json?.confidence || {}
      const header = extractedDraft.draft_json?.header || {}

      // Parse raw date strings for ambiguity detection
      const rawDocDate = extractedDraft.doc_date_confirmed || extractedDraft.doc_date_guess || ''
      const rawDueDate = header.due_date || ''

      // Check for date interpretations
      const docDateInterps = parseAmbiguousDate(rawDocDate)
      const dueDateInterps = parseAmbiguousDate(rawDueDate)

      setRawDateStrings({ doc_date: rawDocDate, due_date: rawDueDate })
      setDateInterpretations({ doc_date: docDateInterps, due_date: dueDateInterps })

      // Use first interpretation as default (or empty if none)
      const resolvedDocDate = docDateInterps.length > 0 ? docDateInterps[0].value : ''
      const resolvedDueDate = dueDateInterps.length > 0 ? dueDateInterps[0].value : ''

      // Parse payment terms - check multiple possible source fields
      const rawTerms = header.payment_terms || header.terms || extractedDraft.draft_json?.payment_terms || ''
      const parsedTerms = parsePaymentTerms(rawTerms)

      // Normalize doc type from OCR to canonical type
      const rawDocType = extractedDraft.doc_type_confirmed || extractedDraft.doc_type_guess || ''
      const contactDir = extractedDraft.counterparty_guess ? undefined : undefined
      const normalizedDocType = normalizeDocType(rawDocType, contactDir)

      setForm({
        doc_type: normalizedDocType,
        counterparty_name: extractedDraft.counterparty_guess || '',
        doc_date: resolvedDocDate,
        due_date: resolvedDueDate,
        currency: extractedDraft.currency_confirmed || extractedDraft.currency_guess || 'GBP',
        invoice_no: extractedDraft.invoice_no_confirmed || extractedDraft.invoice_no_guess || '',
        payment_terms: parsedTerms || '',
        order_no: header.order_no || '',
      })

      // Store extracted vendor details
      const vendor = extractedDraft.draft_json?.vendor
      if (vendor) {
        setExtractedVendor(vendor)
      }

      setFieldConfidence({
        doc_type: headerConfidence.doc_type ?? null,
        counterparty_name: headerConfidence.counterparty ?? null,
        doc_date: headerConfidence.doc_date ?? null,
        currency: headerConfidence.currency ?? null,
        invoice_no: headerConfidence.invoice_no ?? null,
      })

      const nextLines = extractedDraft.lines?.length
        ? extractedDraft.lines.map((line, idx) =>
            formatLine({
              line_no: idx + 1,
              description: line.description_confirmed || line.description_guess || '',
              qty: line.qty || '1.00',
              unit_price: line.unit_price || '0.00',
              net: line.net || '0.00',
              vat: line.vat || '0.00',
              gross: line.gross || '0.00',
              vat_code: line.vat_code_confirmed || line.vat_code_guess || 'VAT20',
              nominal_code: line.nominal_code_confirmed || line.nominal_code_guess || '4000',
              confidence: line.confidence ? parseFloat(line.confidence) : null,
            })
          )
        : [recalcLine(emptyLine(1))]
      setLines(nextLines)

      // Compute persistent document errors from OCR extraction
      // These errors represent discrepancies on the original document and persist through edits
      const docErrors = []
      nextLines.forEach((line, idx) => {
        const qty = toNumber(line.qty)
        const unitPrice = toNumber(line.unit_price)
        const net = toNumber(line.net)
        const vat = toNumber(line.vat)
        const gross = toNumber(line.gross)
        const vatRate = getVatRate(line.vat_code)

        const expectedNet = qty * unitPrice
        if (Math.abs(expectedNet - net) > 0.02 && net !== 0) {
          docErrors.push({
            field: `line_${idx}`,
            lineIndex: idx,
            type: 'net_mismatch',
            message: `Line ${idx + 1} "${line.description}": Net on document (${line.net}) does not equal Qty (${line.qty}) x Unit Price (${line.unit_price}) = ${formatMoney(expectedNet)}`,
            severity: 'error',
            expected: formatMoney(expectedNet),
            actual: line.net,
          })
        }

        const expectedVat = net * vatRate
        if (Math.abs(expectedVat - vat) > 0.02 && vat !== 0) {
          docErrors.push({
            field: `line_${idx}`,
            lineIndex: idx,
            type: 'vat_mismatch',
            message: `Line ${idx + 1} "${line.description}": VAT on document (${line.vat}) does not match expected (${formatMoney(expectedVat)}) at ${(vatRate * 100).toFixed(0)}%`,
            severity: 'error',
            expected: formatMoney(expectedVat),
            actual: line.vat,
          })
        }

        const expectedGross = net + vat
        if (Math.abs(expectedGross - gross) > 0.02 && gross !== 0) {
          docErrors.push({
            field: `line_${idx}`,
            lineIndex: idx,
            type: 'gross_mismatch',
            message: `Line ${idx + 1} "${line.description}": Gross on document (${line.gross}) does not equal Net + VAT (${formatMoney(expectedGross)})`,
            severity: 'error',
            expected: formatMoney(expectedGross),
            actual: line.gross,
          })
        }
      })

      // Document-level total checks
      const draftTotals = extractedDraft.draft_json?.totals || extractedDraft.draft_json?.header || {}
      const extractedSubtotal = toNumber(draftTotals.subtotal || draftTotals.net_total || draftTotals.sub_total || 0)
      const extractedVatTotal = toNumber(draftTotals.vat_total || draftTotals.tax || draftTotals.vat || 0)
      const extractedGrossTotal = toNumber(draftTotals.total || draftTotals.gross_total || draftTotals.total_payable || 0)
      const calcNet = nextLines.reduce((sum, line) => sum + toNumber(line.net), 0)
      const calcVat = nextLines.reduce((sum, line) => sum + toNumber(line.vat), 0)
      const calcGross = nextLines.reduce((sum, line) => sum + toNumber(line.gross), 0)

      if (extractedSubtotal > 0 && Math.abs(extractedSubtotal - calcNet) > 0.02) {
        docErrors.push({
          field: 'totals', type: 'total_net_mismatch',
          message: `Document subtotal (${formatMoney(extractedSubtotal)}) does not match sum of line nets (${formatMoney(calcNet)})`,
          severity: 'error',
        })
      }
      if (extractedVatTotal > 0 && Math.abs(extractedVatTotal - calcVat) > 0.02) {
        docErrors.push({
          field: 'totals', type: 'total_vat_mismatch',
          message: `Document VAT total (${formatMoney(extractedVatTotal)}) does not match sum of line VAT (${formatMoney(calcVat)})`,
          severity: 'error',
        })
      }
      if (extractedGrossTotal > 0 && Math.abs(extractedGrossTotal - calcGross) > 0.02) {
        docErrors.push({
          field: 'totals', type: 'total_gross_mismatch',
          message: `Document total (${formatMoney(extractedGrossTotal)}) does not match sum of line totals (${formatMoney(calcGross)})`,
          severity: 'error',
        })
      }

      setDocumentErrors(docErrors)
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
    setLines((prev) =>
      prev.filter((_, idx) => idx !== index).map((item, idx) => ({
        ...item,
        line_no: idx + 1,
      }))
    )
  }

  const buildPayload = () => ({
    doc_type: form.doc_type || null,
    counterparty_name: form.counterparty_name || null,
    counterparty_id: selectedContact?.id || null,
    doc_date: form.doc_date || null,
    due_date: form.due_date || null,
    currency: form.currency || null,
    invoice_no: form.invoice_no || null,
    payment_terms: form.payment_terms || null,
    order_no: form.order_no || null,
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

  const handleClose = () => {
    // If we're in client context, navigate back to client page
    if (clientId) {
      navigate(`/client/${clientId}`)
      return
    }
    // Otherwise reset state to start fresh
    setDraft(null)
    setInboxItem(null)
    setForm({
      doc_type: '',
      counterparty_name: '',
      doc_date: '',
      due_date: '',
      currency: 'GBP',
      invoice_no: '',
      payment_terms: '',
      order_no: '',
    })
    setFieldConfidence({
      doc_type: null,
      counterparty_name: null,
      doc_date: null,
      currency: null,
      invoice_no: null,
    })
    setLines([recalcLine(emptyLine(1)), recalcLine(emptyLine(2))])
    setDateInterpretations({ doc_date: [], due_date: [] })
    setRawDateStrings({ doc_date: '', due_date: '' })
    setSelectedContact(null)
    setContactMatches([])
    setExtractedVendor(null)
    setShowContactDropdown(false)
  }

  // Determine if we should show the full-screen review mode
  const showReviewMode = inboxItem !== null

  if (!showReviewMode) {
    // Initial upload prompt - centered on screen
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 64px)' }}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 max-w-lg w-full mx-4">
            {/* Client context banner */}
            {clientId && (
              <div className="mb-6">
                <button
                  onClick={() => navigate(`/client/${clientId}`)}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 mb-3"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Client
                </button>
                {loadingClient ? (
                  <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3 text-center">
                    <span className="text-purple-700 dark:text-purple-300 text-sm">Loading client...</span>
                  </div>
                ) : client ? (
                  <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      <div>
                        <div className="font-medium text-purple-900 dark:text-purple-100">{client.name}</div>
                        <div className="text-xs text-purple-600 dark:text-purple-400">
                          Documents will be linked to this client
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            )}

            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 text-center">
              {clientId ? 'AI Document OCR' : 'Document Review'}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-center mb-8">
              Upload a document to begin AI-powered extraction
            </p>

            <label className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl cursor-pointer hover:border-blue-500 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
              <div className="text-center">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-gray-700 dark:text-gray-300 font-medium text-lg">
                  Drop your file here
                </p>
                <p className="text-gray-500 dark:text-gray-500 mt-1">or click to browse</p>
                <p className="text-gray-400 dark:text-gray-600 text-sm mt-4">
                  PDF, JPG, PNG up to 10MB
                </p>
              </div>
              <input
                type="file"
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                disabled={uploading}
              />
            </label>

            {uploading && (
              <div className="mt-4 flex items-center justify-center gap-2 text-blue-600">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Uploading...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Full-screen review mode
  const isCompact = viewMode === 'compact'
  const previewUrl = getFileUrl(inboxItem?.file_url)
  const isImage = inboxItem?.mime_type?.startsWith('image/')
  const isPdf = inboxItem?.mime_type === 'application/pdf'

  return (
    <div className="h-screen flex flex-col bg-gray-100 dark:bg-gray-900 overflow-hidden">
      {/* Header Bar */}
      <header className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleClose}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                {inboxItem?.file_name || 'Document Review'}
              </h1>
              <div className="flex items-center gap-2 text-sm">
                {client && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {client.name}
                  </span>
                )}
                {draft && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
                    {draft.status || 'draft'}
                  </span>
                )}
                <span
                  className={`px-2 py-0.5 text-xs rounded-full ${
                    documentErrors.length === 0 && formIssues.length === 0
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
                      : documentErrors.length > 0 || formIssues.some(i => i.severity === 'error')
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                  }`}
                >
                  {documentErrors.length === 0 && formIssues.length === 0
                    ? 'Valid'
                    : `${documentErrors.length + formIssues.length} issue(s)`}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* View mode toggle */}
            <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setViewMode('full')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  viewMode === 'full'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
                title="Full screen view"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('compact')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  viewMode === 'compact'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
                title="Compact/tablet view"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </button>
            </div>

            {!draft && (
              <button
                type="button"
                onClick={handleExtract}
                disabled={!inboxItem?.id || extracting}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 flex items-center gap-2"
              >
                {extracting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Extracting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    Run AI Extraction
                  </>
                )}
              </button>
            )}

            {draft && (
              <>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-60 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                >
                  {saving ? 'Saving...' : 'Save Draft'}
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-60"
                >
                  {submitting ? 'Submitting...' : 'Submit'}
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className={`flex-1 flex overflow-hidden ${isCompact ? 'flex-col' : ''}`}>
        {/* Document Preview Panel */}
        <section
          className={`bg-gray-200 dark:bg-gray-950 ${
            isCompact ? 'h-1/2 w-full' : 'w-1/2 h-full'
          } flex-shrink-0 overflow-hidden`}
        >
          {previewUrl && isImage ? (
            // Image preview - shown immediately after upload, fetched with auth
            <div className="h-full w-full flex items-center justify-center p-4 overflow-auto">
              <AuthImage url={previewUrl} alt={inboxItem?.file_name} />
            </div>
          ) : previewUrl && isPdf ? (
            // PDF preview - shown immediately after upload
            <PDFPreview url={previewUrl} fileName={inboxItem?.file_name} />
          ) : (
            // No preview available (unsupported format or no URL yet)
            <div className="h-full flex flex-col items-center justify-center p-8">
              <svg
                className="w-20 h-20 text-gray-400 dark:text-gray-600 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.5"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-gray-700 dark:text-gray-300 font-medium text-lg">
                {inboxItem?.file_name}
              </p>
              <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">{inboxItem?.mime_type}</p>
              {!draft && (
                <p className="text-blue-600 dark:text-blue-400 text-sm mt-4">
                  Click "Run AI Extraction" to process this document
                </p>
              )}
              {previewUrl && (
                <a
                  href={previewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Download File
                </a>
              )}
            </div>
          )}
        </section>

        {/* Form Panel */}
        <section
          className={`bg-white dark:bg-gray-800 ${
            isCompact ? 'h-1/2 w-full' : 'w-1/2 h-full'
          } overflow-y-auto`}
        >
          {!draft ? (
            <div className="p-6 flex flex-col items-center justify-center h-full text-center">
              <svg className="w-16 h-16 text-blue-400 dark:text-blue-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Ready for Extraction
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-sm">
                Review the document preview on the left, then click
                <strong className="text-blue-600 dark:text-blue-400"> Run AI Extraction </strong>
                to extract data from this document.
              </p>
              <button
                type="button"
                onClick={handleExtract}
                disabled={!inboxItem?.id || extracting}
                className="px-6 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 flex items-center gap-2 text-lg"
              >
                {extracting ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Extracting...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    Run AI Extraction
                  </>
                )}
              </button>
            </div>
          ) : (
          <div className="p-6 space-y-6">
            {/* Header Fields - Compact Layout */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                Document Details
              </h2>

              {/* Row 1: Type, Currency, Invoice #, Order # */}
              <div className="grid grid-cols-4 gap-3 mb-3">
                <div>
                  <label className={`block text-xs font-medium mb-1 ${fieldErrors.doc_type ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>Type</label>
                  <select
                    value={form.doc_type}
                    onChange={(e) => setForm((prev) => ({ ...prev, doc_type: e.target.value }))}
                    className={`w-full px-2 py-1.5 text-sm border rounded bg-white dark:bg-gray-700 ${fieldErrors.doc_type ? 'border-red-400 dark:border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                  >
                    <option value="">Select</option>
                    {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Currency</label>
                  <select
                    value={form.currency}
                    onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value }))}
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  >
                    {CURRENCIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className={`block text-xs font-medium mb-1 ${fieldErrors.invoice_no ? 'text-amber-500' : 'text-gray-500 dark:text-gray-400'}`}>Ref #</label>
                  <input
                    type="text"
                    value={form.invoice_no}
                    onChange={(e) => setForm((prev) => ({ ...prev, invoice_no: e.target.value }))}
                    placeholder="INV-001"
                    className={`w-full px-2 py-1.5 text-sm border rounded bg-white dark:bg-gray-700 ${fieldErrors.invoice_no ? 'border-amber-400 dark:border-amber-500' : 'border-gray-300 dark:border-gray-600'}`}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Order #</label>
                  <input
                    type="text"
                    value={form.order_no}
                    onChange={(e) => setForm((prev) => ({ ...prev, order_no: e.target.value }))}
                    placeholder="PO-001"
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  />
                </div>
              </div>

              {/* Row 2: Contact (Vendor/Customer) with matching */}
              <div className="mb-3">
                <label className={`block text-xs font-medium mb-1 ${fieldErrors.counterparty_name ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>
                  Contact (Vendor/Customer)
                  {selectedContact && (
                    <span className="ml-2 text-green-600 dark:text-green-400 text-xs">
                      (Matched: {selectedContact.name})
                    </span>
                  )}
                </label>
                <div className="flex gap-2">
                  <div className="flex-1 relative" ref={vendorDropdownRef}>
                    <input
                      type="text"
                      value={form.counterparty_name}
                      onChange={(e) => {
                        setForm((prev) => ({ ...prev, counterparty_name: e.target.value }))
                        setShowContactDropdown(true)
                        setSelectedContact(null)
                      }}
                      onFocus={() => setShowContactDropdown(true)}
                      placeholder="Start typing contact name..."
                      className={`w-full px-2 py-1.5 text-sm border rounded bg-white dark:bg-gray-700 ${
                        fieldErrors.counterparty_name ? 'border-red-400 dark:border-red-500'
                        : selectedContact ? 'border-green-400 dark:border-green-500'
                        : 'border-gray-300 dark:border-gray-600'
                      }`}
                    />
                    {/* Contact matches dropdown */}
                    {showContactDropdown && contactMatches.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-auto">
                        <div className="px-2 py-1 text-xs text-gray-500 border-b dark:border-gray-700">
                          Possible matches:
                        </div>
                        {contactMatches.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex justify-between items-center"
                            onClick={() => {
                              setForm((prev) => ({ ...prev, counterparty_name: c.name }))
                              setSelectedContact(c)
                              setShowContactDropdown(false)
                            }}
                          >
                            <div>
                              <span>{c.name}</span>
                              {c.contact_type && (
                                <span className="ml-2 text-xs text-gray-400">({c.contact_type})</span>
                              )}
                            </div>
                            <span className="text-xs text-gray-400">{Math.round(c.score * 100)}%</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {/* Save new contact button */}
                  {form.counterparty_name && !selectedContact && contactMatches.length === 0 && clientId && (
                    <button
                      type="button"
                      className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 whitespace-nowrap"
                      onClick={async () => {
                        try {
                          const contactData = {
                            name: form.counterparty_name,
                            contact_type: DOC_TYPE_CONTACT_DIR[form.doc_type] || 'vendor',
                            ...(extractedVendor || {}),
                          }
                          await clientsAPI.createContact(clientId, contactData)
                          addToast(`Contact "${form.counterparty_name}" saved`, 'success')
                          // Refresh contacts
                          const contactsRes = await clientsAPI.getContacts(clientId, { limit: 500 })
                          setContacts(contactsRes.data.contacts || [])
                        } catch (e) {
                          addToast('Failed to save contact', 'error')
                        }
                      }}
                    >
                      + Save Contact
                    </button>
                  )}
                </div>
                {/* Extracted contact details preview */}
                {extractedVendor && (
                  <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-xs text-gray-600 dark:text-gray-400">
                    <div className="font-medium text-gray-700 dark:text-gray-300 mb-1">Extracted Details:</div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                      {extractedVendor.address_line1 && <div>{extractedVendor.address_line1}</div>}
                      {extractedVendor.city && <div>{extractedVendor.city} {extractedVendor.postcode}</div>}
                      {extractedVendor.vat_number && <div>VAT: {extractedVendor.vat_number}</div>}
                      {extractedVendor.email && <div>{extractedVendor.email}</div>}
                    </div>
                  </div>
                )}
              </div>

              {/* Row 3: Dates and Payment Terms */}
              <div className="grid grid-cols-3 gap-3">
                {/* Invoice Date with ambiguity dropdown */}
                <div>
                  <label className={`block text-xs font-medium mb-1 ${fieldErrors.doc_date ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}>
                    Invoice Date
                    {dateInterpretations.doc_date?.length > 1 && (
                      <span className="ml-1 text-amber-500" title="Ambiguous date format">⚠</span>
                    )}
                  </label>
                  {dateInterpretations.doc_date?.length > 1 ? (
                    <select
                      value={form.doc_date}
                      onChange={(e) => setForm((prev) => ({ ...prev, doc_date: e.target.value }))}
                      className="w-full px-2 py-1.5 text-sm border border-amber-400 dark:border-amber-500 rounded bg-white dark:bg-gray-700"
                    >
                      {dateInterpretations.doc_date.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="date"
                      value={form.doc_date || ''}
                      onChange={(e) => setForm((prev) => ({ ...prev, doc_date: e.target.value }))}
                      className={`w-full px-2 py-1.5 text-sm border rounded bg-white dark:bg-gray-700 ${fieldErrors.doc_date ? 'border-red-400 dark:border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                    />
                  )}
                </div>

                {/* Payment Terms */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Terms</label>
                  <select
                    value={form.payment_terms}
                    onChange={(e) => setForm((prev) => ({ ...prev, payment_terms: e.target.value }))}
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  >
                    <option value="">Select</option>
                    {PAYMENT_TERMS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>

                {/* Due Date */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Due Date
                    {form.payment_terms && form.payment_terms !== 'custom' && (
                      <span className="ml-1 text-green-500 text-xs">(auto)</span>
                    )}
                  </label>
                  <input
                    type="date"
                    value={form.due_date || ''}
                    onChange={(e) => setForm((prev) => ({ ...prev, due_date: e.target.value, payment_terms: 'custom' }))}
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                  />
                </div>
              </div>
            </div>

            {/* Line Items */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Line Items</h2>
                <button
                  type="button"
                  onClick={addLine}
                  className="text-sm px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                  Add Line
                </button>
              </div>

              <div className="overflow-x-auto -mx-6 px-6">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                      <th className="py-2 pr-2 font-medium">Description</th>
                      <th className="py-2 pr-2 font-medium w-16">Qty</th>
                      <th className="py-2 pr-2 font-medium w-24">Unit Price</th>
                      <th className="py-2 pr-2 font-medium w-28">VAT Code</th>
                      <th className="py-2 pr-2 font-medium w-36">Nominal</th>
                      <th className="py-2 pr-2 font-medium text-right w-20">Net</th>
                      <th className="py-2 pr-2 font-medium text-right w-20">VAT</th>
                      <th className="py-2 pr-2 font-medium text-right w-20">Gross</th>
                      <th className="py-2 w-8"></th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-800 dark:text-gray-200">
                    {lines.map((line, index) => (
                      <tr
                        key={index}
                        className="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                      >
                        <td className="py-2 pr-2">
                          <div className="relative">
                            <input
                              type="text"
                              value={line.description}
                              onChange={(e) => updateLine(index, 'description', e.target.value)}
                              className={`w-full min-w-[200px] px-2 py-1.5 border rounded bg-white dark:bg-gray-700 text-sm ${
                                fieldErrors[`line_${index}_desc`]
                                  ? 'border-red-400 dark:border-red-500'
                                  : line.confidence !== null && line.confidence < CONFIDENCE_THRESHOLD
                                  ? 'border-amber-400 dark:border-amber-500'
                                  : 'border-gray-300 dark:border-gray-600'
                              }`}
                              placeholder="Line description"
                            />
                            {line.confidence !== null && line.confidence < CONFIDENCE_THRESHOLD && (
                              <span
                                className="absolute right-1 top-1/2 -translate-y-1/2 text-amber-500"
                                title={`AI confidence: ${Math.round((line.confidence || 0) * 100)}%`}
                              >
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                  <path
                                    fillRule="evenodd"
                                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2 pr-2">
                          <input
                            type="number"
                            min="0"
                            step="1"
                            value={line.qty}
                            onChange={(e) => updateLine(index, 'qty', e.target.value)}
                            className="w-16 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-sm"
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={line.unit_price}
                            onChange={(e) => updateLine(index, 'unit_price', e.target.value)}
                            className="w-24 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-sm"
                          />
                        </td>
                        <td className="py-2 pr-2">
                          <select
                            value={line.vat_code}
                            onChange={(e) => updateLine(index, 'vat_code', e.target.value)}
                            className="w-28 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-sm"
                          >
                            {VAT_CODES.map((code) => (
                              <option key={code.value} value={code.value}>
                                {code.label}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 pr-2">
                          <select
                            value={line.nominal_code}
                            onChange={(e) => updateLine(index, 'nominal_code', e.target.value)}
                            className="w-36 px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-sm"
                          >
                            {nominalCodeOptions.map((code) => (
                              <option key={code.value} value={code.value}>
                                {code.label}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className={`py-2 pr-2 text-right font-mono ${fieldErrors[`line_${index}_net`] ? 'text-red-600 dark:text-red-400 font-semibold' : ''}`}>{line.net}</td>
                        <td className={`py-2 pr-2 text-right font-mono ${fieldErrors[`line_${index}_vat`] ? 'text-red-600 dark:text-red-400 font-semibold' : ''}`}>{line.vat}</td>
                        <td className={`py-2 pr-2 text-right font-mono ${fieldErrors[`line_${index}_gross`] ? 'text-red-600 dark:text-red-400 font-semibold' : ''}`}>{line.gross}</td>
                        <td className="py-2">
                          <button
                            type="button"
                            onClick={() => removeLine(index)}
                            className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-30"
                            disabled={lines.length <= 1}
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Totals */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="flex justify-end">
                <div className="w-64 space-y-2 text-sm">
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Net Total</span>
                    <span className="font-mono">{form.currency} {totals.net}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>VAT</span>
                    <span className="font-mono">{form.currency} {totals.vat}</span>
                  </div>
                  <div className="flex justify-between text-lg font-semibold text-gray-900 dark:text-white border-t border-gray-200 dark:border-gray-700 pt-2">
                    <span>Gross Total</span>
                    <span className="font-mono">{form.currency} {totals.gross}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Document Errors - persistent, from original OCR extraction */}
            {documentErrors.length > 0 && (
              <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-800/50 dark:bg-red-900/20 p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <p className="font-semibold mb-1 text-red-800 dark:text-red-300">
                      {documentErrors.length} Document Error{documentErrors.length !== 1 ? 's' : ''} Found
                    </p>
                    <p className="text-xs text-red-600 dark:text-red-400 mb-2">
                      These errors were found on the original document and persist for querying the contact.
                    </p>
                    <ul className="space-y-1 text-sm">
                      {documentErrors.map((err, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-red-700 dark:text-red-300">
                          <span className="flex-shrink-0 mt-0.5">●</span>
                          <span>{err.message}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Form Issues - dynamic, changes as user edits */}
            {formIssues.length > 0 && (
              <div className={`rounded-lg border p-4 ${
                formIssues.some(i => i.severity === 'error')
                  ? 'border-amber-200 bg-amber-50 dark:border-amber-800/50 dark:bg-amber-900/20'
                  : 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50'
              }`}>
                <div className="flex items-start gap-3">
                  <svg className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                    formIssues.some(i => i.severity === 'error') ? 'text-amber-500' : 'text-gray-400'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="flex-1">
                    <p className="font-semibold mb-1 text-gray-900 dark:text-white">
                      Form: {formIssues.filter(i => i.severity === 'error').length} Error(s),{' '}
                      {formIssues.filter(i => i.severity === 'warning').length} Warning(s)
                    </p>
                    <ul className="space-y-1 text-sm">
                      {formIssues.map((issue, idx) => (
                        <li key={idx} className={`flex items-start gap-2 ${
                          issue.severity === 'error'
                            ? 'text-amber-700 dark:text-amber-300'
                            : 'text-gray-600 dark:text-gray-400'
                        }`}>
                          <span className="flex-shrink-0 mt-0.5">
                            {issue.severity === 'error' ? '●' : '○'}
                          </span>
                          {issue.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Debug Panel - Extracted Data */}
            {draft?.draft_json && (
              <details className="rounded-lg border border-gray-200 dark:border-gray-700">
                <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  Debug: Raw Extracted Data
                </summary>
                <div className="px-4 pb-4 space-y-4">
                  {/* Vendor Details */}
                  {draft.draft_json.vendor && (
                    <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-3">
                      <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">Vendor (Seller)</h4>
                      <dl className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
                        <div className="flex"><dt className="w-24 font-medium">Name:</dt><dd>{draft.draft_json.vendor.name || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Address 1:</dt><dd>{draft.draft_json.vendor.address_line1 || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Address 2:</dt><dd>{draft.draft_json.vendor.address_line2 || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">City:</dt><dd>{draft.draft_json.vendor.city || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Postcode:</dt><dd>{draft.draft_json.vendor.postcode || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Country:</dt><dd>{draft.draft_json.vendor.country || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">VAT #:</dt><dd>{draft.draft_json.vendor.vat_number || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Phone:</dt><dd>{draft.draft_json.vendor.phone || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Email:</dt><dd>{draft.draft_json.vendor.email || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Website:</dt><dd>{draft.draft_json.vendor.website || '-'}</dd></div>
                      </dl>
                    </div>
                  )}

                  {/* Customer Details */}
                  {draft.draft_json.customer && (
                    <div className="rounded-lg bg-green-50 dark:bg-green-900/20 p-3">
                      <h4 className="text-sm font-semibold text-green-800 dark:text-green-300 mb-2">Customer (Buyer)</h4>
                      <dl className="text-xs text-green-700 dark:text-green-400 space-y-1">
                        <div className="flex"><dt className="w-24 font-medium">Name:</dt><dd>{draft.draft_json.customer.name || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Address 1:</dt><dd>{draft.draft_json.customer.address_line1 || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Address 2:</dt><dd>{draft.draft_json.customer.address_line2 || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">City:</dt><dd>{draft.draft_json.customer.city || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Postcode:</dt><dd>{draft.draft_json.customer.postcode || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Country:</dt><dd>{draft.draft_json.customer.country || '-'}</dd></div>
                        <div className="flex"><dt className="w-24 font-medium">Reference:</dt><dd>{draft.draft_json.customer.reference || '-'}</dd></div>
                      </dl>
                    </div>
                  )}

                  {/* Additional Header Info */}
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-700/50 p-3">
                    <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-300 mb-2">Additional Info</h4>
                    <dl className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                      <div className="flex"><dt className="w-24 font-medium">Order #:</dt><dd>{draft.draft_json.header?.order_no || '-'}</dd></div>
                      <div className="flex"><dt className="w-24 font-medium">Terms:</dt><dd>{draft.draft_json.header?.payment_terms || '-'}</dd></div>
                      <div className="flex"><dt className="w-24 font-medium">Status:</dt><dd>{draft.draft_json.header?.payment_status || '-'}</dd></div>
                      <div className="flex"><dt className="w-24 font-medium">Confidence:</dt><dd>{draft.draft_json.confidence ? `${Math.round(parseFloat(draft.draft_json.confidence) * 100)}%` : '-'}</dd></div>
                    </dl>
                  </div>

                  {/* Raw Text */}
                  {draft.draft_json.raw_text && (
                    <div className="rounded-lg bg-gray-50 dark:bg-gray-700/50 p-3">
                      <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-300 mb-2">Raw Text / Notes</h4>
                      <pre className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{draft.draft_json.raw_text}</pre>
                    </div>
                  )}

                  {/* Full JSON */}
                  <details className="rounded-lg bg-gray-100 dark:bg-gray-800">
                    <summary className="px-3 py-2 cursor-pointer text-xs font-medium text-gray-600 dark:text-gray-400">
                      Show Full JSON
                    </summary>
                    <pre className="px-3 pb-3 text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
                      {JSON.stringify(draft.draft_json, null, 2)}
                    </pre>
                  </details>
                </div>
              </details>
            )}
          </div>
          )}
        </section>
      </main>
    </div>
  )
}
